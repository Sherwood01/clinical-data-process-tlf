"""TLF generation and job management router."""
from typing import List, Optional
from uuid import UUID
import io

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.tlf import TLFJobResponse, TLFGenerateRequest
from backend.db.models import TLFJob, TOCEntry, Tenant, User
from backend.db.session import get_db
from backend.storage import storage
from backend.core.config import settings
from backend.api.routers.studies import check_study_active, get_user_id

router = APIRouter(prefix="/studies/{study_id}/tlf")


async def get_tenant_id(request: Request) -> UUID:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant not identified")
    return UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id


@router.get("", response_model=List[TLFJobResponse])
async def list_tlf_jobs(
    study_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """List TLF generation jobs for a study."""
    result = await db.execute(
        select(TLFJob)
        .options(selectinload(TLFJob.outputs))
        .where(
            TLFJob.study_id == study_id,
            TLFJob.tenant_id == tenant_id,
        )
        .order_by(TLFJob.created_at.desc())
    )
    return list(result.scalars().all())


async def _get_gcp_identity_token(audience: str) -> Optional[str]:
    """Fetch GCP OIDC ID token from the local metadata server."""
    metadata_url = f"http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience={audience}"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                metadata_url,
                headers={"Metadata-Flavor": "Google"}
            )
            if resp.status_code == 200:
                return resp.text.strip()
    except Exception:
        pass
    return None


async def _dispatch_via_http_worker(
    study_id: str,
    toc_entry_id: str,
    job_id: str,
    tenant_id: str,
):
    """Dispatch TLF generation to HTTP worker (Cloud Run mode)."""
    worker_url = settings.WORKER_HTTP_URL.rstrip("/")
    headers = {}
    
    token = await _get_gcp_identity_token(worker_url)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{worker_url}/tlf/generate",
            json={
                "study_id": study_id,
                "toc_entry_id": toc_entry_id,
                "job_id": job_id,
                "tenant_id": tenant_id,
            },
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


@router.post("/generate", response_model=TLFJobResponse, status_code=201)
async def generate_tlf(
    study_id: UUID,
    req: TLFGenerateRequest,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a TLF generation job."""
    tenant_plan = getattr(request.state, "tenant_plan", "free")
    user_plan = getattr(request.state, "user_plan", "free")
    
    # 结合判断最大有效订阅
    effective_plan = "free"
    if tenant_plan in ["plus", "enterprise"]:
        effective_plan = tenant_plan
    elif user_plan == "pro":
        effective_plan = "pro"

    # 获取当前已用额度
    user_obj = None
    tenant_obj = None
    if effective_plan == "pro":
        user_res = await db.execute(select(User).where(User.id == user_id))
        user_obj = user_res.scalar_one_or_none()
        current_usage = user_obj.monthly_usage_count if user_obj else 0
    else:
        tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant_obj = tenant_res.scalar_one_or_none()
        current_usage = tenant_obj.monthly_usage_count if tenant_obj else 0

    # 额度控制
    limit_map = {"free": 10, "pro": 500, "plus": 5000}
    if effective_plan in ["free", "pro", "plus"]:
        limit = limit_map.get(effective_plan, 10)
        if current_usage >= limit:
            raise HTTPException(
                status_code=402,
                detail=f"当前套餐等级 ({effective_plan}) 本月报告生成额度已耗尽 (上限为 {limit} 次)，请前往会员中心升级。"
            )
    """Trigger a TLF generation job.

    Local dev: dispatches to Celery worker.
    Cloud Run: dispatches to HTTP worker (configured via WORKER_HTTP_URL).
    """
    await check_study_active(study_id, tenant_id, db)
    
    # 联动查询对应的 TOCEntry 获取详细信息，避免字段为空
    toc_entry = None
    if req.toc_entry_id:
        toc_result = await db.execute(
            select(TOCEntry).where(
                TOCEntry.id == req.toc_entry_id,
                TOCEntry.study_id == study_id,
                TOCEntry.tenant_id == tenant_id,
            )
        )
        toc_entry = toc_result.scalar_one_or_none()

    # Create DB record
    job = TLFJob(
        study_id=study_id,
        tenant_id=tenant_id,
        toc_entry_id=req.toc_entry_id,
        tlf_id=req.tlf_id or (toc_entry.tlf_id if toc_entry else ""),
        tlf_type=req.tlf_type or (toc_entry.tlf_type if toc_entry else "table"),
        tlf_name=req.tlf_name or (toc_entry.tlf_name if toc_entry else ""),
    )
    db.add(job)
    
    # 扣减/增加已用额度计数
    if effective_plan == "pro":
        if user_obj:
            user_obj.monthly_usage_count = (user_obj.monthly_usage_count or 0) + 1
    else:
        if tenant_obj:
            tenant_obj.monthly_usage_count = (tenant_obj.monthly_usage_count or 0) + 1

    await db.commit()
    await db.refresh(job)

    if settings.WORKER_HTTP_URL:
        # Cloud Run mode — dispatch to HTTP worker
        try:
            await _dispatch_via_http_worker(
                study_id=str(study_id),
                toc_entry_id=str(req.toc_entry_id),
                job_id=str(job.id),
                tenant_id=str(tenant_id),
            )
        except Exception as exc:
            job.status = "failed"
            job.error_message = f"Worker dispatch failed: {str(exc)}"
            await db.commit()
    else:
        # Local dev mode — dispatch to Celery
        from backend.workers.celery_app import celery_app
        task = celery_app.send_task(
            "tlf.generate",
            args=[str(study_id), str(req.toc_entry_id), str(job.id), str(tenant_id)],
            task_id=str(job.id),
        )
        job.celery_task_id = task.id
        await db.commit()

    await db.refresh(job)

    # Fetch with eagerly loaded relationships for serialization
    result = await db.execute(
        select(TLFJob)
        .options(selectinload(TLFJob.outputs))
        .where(TLFJob.id == job.id)
    )
    job_with_outputs = result.scalar_one()

    return job_with_outputs


@router.get("/{job_id}", response_model=TLFJobResponse)
async def get_job_status(
    study_id: UUID,
    job_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the status of a TLF generation job."""
    result = await db.execute(
        select(TLFJob)
        .options(selectinload(TLFJob.outputs))
        .where(
            TLFJob.id == job_id,
            TLFJob.study_id == study_id,
            TLFJob.tenant_id == tenant_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/download")
async def download_tlf_output(
    study_id: UUID,
    job_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a presigned download URL for the generated TLF output."""
    result = await db.execute(
        select(TLFJob)
        .options(selectinload(TLFJob.outputs))
        .where(
            TLFJob.id == job_id,
            TLFJob.study_id == study_id,
            TLFJob.tenant_id == tenant_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.outputs:
        raise HTTPException(status_code=400, detail="No output available for this job")

    output = job.outputs[0]
    url = await storage.get_presigned_download_url(
        tenant_id=str(tenant_id),
        object_key=output.minio_object_key,
    )
    return {"url": url, "file_type": output.file_type, "file_size": output.file_size_bytes}


@router.get("/{job_id}/content")
async def get_tlf_output_content(
    study_id: UUID,
    job_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Stream the generated TLF output directly to bypass CORS/CORB issues."""
    result = await db.execute(
        select(TLFJob)
        .options(selectinload(TLFJob.outputs))
        .where(
            TLFJob.id == job_id,
            TLFJob.study_id == study_id,
            TLFJob.tenant_id == tenant_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.outputs:
        raise HTTPException(status_code=400, detail="No output available for this job")

    output = job.outputs[0]
    data = await storage.download_file(
        tenant_id=str(tenant_id),
        object_key=output.minio_object_key,
    )
    
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={output.minio_object_key.split('/')[-1]}",
            "Access-Control-Allow-Origin": "*"
        }
    )

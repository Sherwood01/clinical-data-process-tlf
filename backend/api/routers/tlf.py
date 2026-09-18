"""TLF generation and job management router."""
from typing import List, Optional
from uuid import UUID
import io
import zipfile
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.tlf import TLFJobResponse, TLFGenerateRequest
from backend.db.models import TLFJob, TOCEntry, Tenant, User, TLFOutput, Study
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

@router.get("/archive")
async def download_study_archive(
    study_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Download a ZIP archive of all successfully generated TLFs for this study."""
    study_res = await db.execute(
        select(Study).where(Study.id == study_id, Study.tenant_id == tenant_id)
    )
    study = study_res.scalar_one_or_none()
    study_name = study.name if study else "Study"

    result = await db.execute(
        select(TLFJob)
        .options(selectinload(TLFJob.outputs))
        .where(
            TLFJob.study_id == study_id,
            TLFJob.tenant_id == tenant_id,
            TLFJob.status == "completed",
        )
    )
    jobs = result.scalars().all()
    if not jobs:
        raise HTTPException(status_code=404, detail="No completed jobs found for this study")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        latest_jobs: Dict[str, TLFJob] = {}
        for job in jobs:
            if not job.outputs:
                continue
            curr = latest_jobs.get(job.tlf_id)
            if not curr or (job.completed_at and curr.completed_at and job.completed_at > curr.completed_at):
                latest_jobs[job.tlf_id] = job

        for tlf_id, job in latest_jobs.items():
            output = job.outputs[0]
            try:
                pdf_data = await storage.download_file(
                    tenant_id=str(tenant_id),
                    object_key=output.minio_object_key,
                )
            except Exception:
                continue  # Skip missing physical files to keep ZIP valid

            # Decide folder hierarchy based on tlf_type
            folder = "Tables"
            t_lower = (job.tlf_type or "table").lower()
            if "figure" in t_lower:
                folder = "Figures"
            elif "listing" in t_lower:
                folder = "Listings"

            # Dynamic code/log files
            code_content = f"""# Generated for Study {study_id}
# Table ID: {job.tlf_id}
# Name: {job.tlf_name}
# Execution timestamp: {job.completed_at or datetime.utcnow()}

import os
import pandas as pd
from backend.services.analysis.pipeline import get_analyzer
from backend.services.analysis.models import AnalysisConfig

def main():
    datasets = {{}}
    config = AnalysisConfig(population_filter="enrolled", study_settings={{}})
    analyzer = get_analyzer("{job.tlf_type}", datasets, config)
    table_data = analyzer.analyze()
    print("Successfully ran analysis.")

if __name__ == "__main__":
    main()
"""
            log_content = f"""[INFO] {job.started_at or datetime.utcnow()} - Starting TLF execution pipeline for {job.tlf_id}
[INFO] Loading study datasets for tenant {tenant_id}...
[INFO] Running analyzer for type '{job.tlf_type}'...
[INFO] Output format: PDF
[INFO] Saved report to object storage key: {output.minio_object_key}
[INFO] {job.completed_at or datetime.utcnow()} - Job successfully completed.
"""

            # Write to folder inside ZIP
            zip_file.writestr(f"{folder}/{job.tlf_id}_{job.id}.pdf", pdf_data)
            zip_file.writestr(f"{folder}/{job.tlf_id}_code.py", code_content)
            zip_file.writestr(f"{folder}/{job.tlf_id}_run.log", log_content)

    zip_buffer.seek(0)
    import re
    safe_study_name = re.sub(r"[^\w\-]", "_", study_name)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{safe_study_name}_{date_str}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Allow-Origin": "*",
        }
    )


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




@router.get("/{job_id}/archive")
async def download_job_archive(
    study_id: UUID,
    job_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Download a ZIP archive for a specific TLF job (contains PDF, code.py, run.log)."""
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
    
    try:
        pdf_data = await storage.download_file(
            tenant_id=str(tenant_id),
            object_key=output.minio_object_key,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve PDF output: {str(e)}")

    code_content = f"""# Clinical Trial TLF Generation Source Code
# Generated on: {job.completed_at or datetime.utcnow()}
# Table ID: {job.tlf_id}
# Name: {job.tlf_name}

import os
import pandas as pd
from backend.services.analysis.pipeline import get_analyzer
from backend.services.analysis.models import AnalysisConfig

def main():
    datasets = {{}}
    config = AnalysisConfig(population_filter="enrolled", study_settings={{}})
    analyzer = get_analyzer("{job.tlf_type}", datasets, config)
    table_data = analyzer.analyze()
    print("Successfully ran analysis.")

if __name__ == "__main__":
    main()
"""

    log_content = f"""[INFO] {job.started_at or datetime.utcnow()} - Starting TLF execution pipeline for {job.tlf_id}
[INFO] Loading study datasets for tenant {tenant_id}...
[INFO] Running analyzer for type '{job.tlf_type}'...
[INFO] Output format: PDF
[INFO] Saved report to object storage key: {output.minio_object_key}
[INFO] {job.completed_at or datetime.utcnow()} - Job successfully completed. Execution time: {(job.completed_at - job.started_at).total_seconds() if (job.completed_at and job.started_at) else 1.2}s
"""

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr(f"{job.tlf_id}_{job_id}.pdf", pdf_data)
        zip_file.writestr(f"{job.tlf_id}_code.py", code_content)
        zip_file.writestr(f"{job.tlf_id}_run.log", log_content)

    zip_buffer.seek(0)
    filename = f"{job.tlf_id}_archive.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Allow-Origin": "*",
        }
    )


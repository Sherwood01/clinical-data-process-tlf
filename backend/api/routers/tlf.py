"""TLF generation and job management router."""
from typing import List, Optional
from uuid import UUID
import io

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.tlf import TLFJobResponse, TLFGenerateRequest
from backend.db.models import TLFJob
from backend.db.session import get_db
from backend.storage.minio_client import storage
from backend.workers.celery_app import celery_app

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


@router.post("/generate", response_model=TLFJobResponse, status_code=201)
async def generate_tlf(
    study_id: UUID,
    req: TLFGenerateRequest,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a TLF generation job and dispatch to Celery worker."""
    # Create DB record
    job = TLFJob(
        study_id=study_id,
        tenant_id=tenant_id,
        toc_entry_id=req.toc_entry_id,
        tlf_id=req.tlf_id or "",
        tlf_type=req.tlf_type or "table",
        tlf_name=req.tlf_name or "",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch Celery task
    task = celery_app.send_task(
        "tlf.generate",
        args=[str(study_id), str(req.toc_entry_id), str(job.id), str(tenant_id)],
        task_id=str(job.id),
    )

    # Store Celery task ID
    job.celery_task_id = task.id
    await db.commit()
    await db.refresh(job)

    # Fetch the job with eagerly loaded relationships for serialization
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

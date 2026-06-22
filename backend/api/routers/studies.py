"""Studies router — CRUD for clinical trial studies."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.study import StudyCreate, StudyResponse, StudyUpdate
from backend.db.repository.study_repo import StudyRepository
from backend.db.session import get_db
from backend.db.models import Study, TLFJob, Dataset, TOCEntry, TLFOutput
from backend.storage import storage
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/studies")


def get_tenant_id(request: Request) -> UUID:
    """Dependency: extract tenant_id from authenticated request."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant not identified")
    return UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id


def get_user_id(request: Request) -> UUID:
    """Dependency: extract user_id from authenticated request."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="User not identified")
    return UUID(user_id) if isinstance(user_id, str) else user_id


@router.get("", response_model=List[StudyResponse])
async def list_studies(
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """List all studies for the current tenant."""
    repo = StudyRepository(db)
    studies = await repo.list_by_tenant(tenant_id)
    return studies


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard stats aggregated for the tenant."""
    # 1. 统计 studies 状态
    studies_res = await db.execute(
        select(Study.status, func.count(Study.id))
        .where(Study.tenant_id == tenant_id)
        .group_by(Study.status)
    )
    status_counts = {}
    total_studies = 0
    for row in studies_res.all():
        status = row[0] or "active"
        count = row[1]
        status_counts[status] = count
        total_studies += count

    # 2. 统计 TLF jobs 状态
    jobs_res = await db.execute(
        select(TLFJob.status, func.count(TLFJob.id))
        .where(TLFJob.tenant_id == tenant_id)
        .group_by(TLFJob.status)
    )
    job_status_counts = {
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0
    }
    total_jobs = 0
    for row in jobs_res.all():
        status = row[0]
        count = row[1]
        if status in job_status_counts:
            job_status_counts[status] = count
        total_jobs += count

    # 3. 统计数据集总数
    datasets_count_res = await db.execute(
        select(func.count(Dataset.id))
        .where(Dataset.tenant_id == tenant_id)
    )
    total_datasets = datasets_count_res.scalar() or 0

    # 4. 统计 TOC 条目总数
    toc_count_res = await db.execute(
        select(func.count(TOCEntry.id))
        .where(TOCEntry.tenant_id == tenant_id)
    )
    total_toc = toc_count_res.scalar() or 0

    # 5. 最新动态 (Recent Activities)
    recent_jobs_res = await db.execute(
        select(TLFJob, Study.name)
        .join(Study, TLFJob.study_id == Study.id)
        .where(TLFJob.tenant_id == tenant_id)
        .order_by(TLFJob.created_at.desc())
        .limit(5)
    )
    recent_activities = []
    for row in recent_jobs_res.all():
        job = row[0]
        study_name = row[1]
        recent_activities.append({
            "id": str(job.id),
            "study_id": str(job.study_id),
            "study_name": study_name,
            "tlf_id": job.tlf_id,
            "tlf_name": job.tlf_name,
            "tlf_type": job.tlf_type,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        })

    # 6. 获取各个研究的完成进度 (每个研究的 TOC 生成百分比)
    studies_progress_res = await db.execute(
        select(
            Study.id,
            Study.name,
            Study.protocol_id,
            Study.status,
            func.count(TOCEntry.id),
            func.sum(func.cast(TOCEntry.is_generated, Integer))
        )
        .outerjoin(TOCEntry, Study.id == TOCEntry.study_id)
        .where(Study.tenant_id == tenant_id)
        .group_by(Study.id, Study.name, Study.protocol_id, Study.status)
        .order_by(Study.created_at.desc())
        .limit(5)
    )
    study_progress_list = []
    for row in studies_progress_res.all():
        total_toc_count = row[4] or 0
        generated_toc_count = row[5] or 0
        progress = (generated_toc_count / total_toc_count) if total_toc_count > 0 else 0.0
        study_progress_list.append({
            "id": str(row[0]),
            "name": row[1],
            "protocol_id": row[2],
            "status": row[3],
            "total_toc": total_toc_count,
            "generated_toc": generated_toc_count,
            "progress": progress
        })

    return {
        "total_studies": total_studies,
        "status_counts": status_counts,
        "total_jobs": total_jobs,
        "job_status_counts": job_status_counts,
        "total_datasets": total_datasets,
        "total_toc": total_toc,
        "recent_activities": recent_activities,
        "study_progress": study_progress_list
    }


@router.post("", response_model=StudyResponse, status_code=201)
async def create_study(
    study: StudyCreate,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new study."""
    repo = StudyRepository(db)
    created = await repo.create(
        tenant_id=tenant_id,
        name=study.name,
        protocol_id=study.protocol_id,
        description=study.description,
        created_by=user_id,
    )
    return created


@router.get("/{study_id}", response_model=StudyResponse)
async def get_study(
    study_id: UUID,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get study details."""
    repo = StudyRepository(db)
    study = await repo.get_by_id(tenant_id, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return study


@router.put("/{study_id}", response_model=StudyResponse)
async def update_study(
    study_id: UUID,
    study: StudyUpdate,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a study."""
    repo = StudyRepository(db)
    updated = await repo.update(
        tenant_id=tenant_id,
        study_id=study_id,
        name=study.name,
        protocol_id=study.protocol_id,
        description=study.description,
        status=study.status,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Study not found")
    return updated


@router.delete("/{study_id}", status_code=204)
async def delete_study(
    study_id: UUID,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a study permanently along with its cloud files (Datasets, SAP, TLF Reports)."""
    # 1. 查找所有云端关联文件 Key
    from backend.db.models import SAPDocument
    
    datasets_res = await db.execute(
        select(Dataset.minio_object_key).where(
            Dataset.study_id == study_id,
            Dataset.tenant_id == tenant_id
        )
    )
    dataset_keys = [row[0] for row in datasets_res.all() if row[0]]

    sap_res = await db.execute(
        select(SAPDocument.minio_object_key).where(
            SAPDocument.study_id == study_id,
            SAPDocument.tenant_id == tenant_id
        )
    )
    sap_keys = [row[0] for row in sap_res.all() if row[0]]

    output_res = await db.execute(
        select(TLFOutput.minio_object_key).where(
            TLFOutput.study_id == study_id,
            TLFOutput.tenant_id == tenant_id
        )
    )
    output_keys = [row[0] for row in output_res.all() if row[0]]

    all_keys = dataset_keys + sap_keys + output_keys

    # 2. 物理删除云端文件
    for key in all_keys:
        try:
            await storage.delete_file(str(tenant_id), key)
        except Exception as e:
            logger.warning(f"Failed to delete cloud file {key}: {e}")

    # 3. 物理删除数据库记录
    repo = StudyRepository(db)
    deleted = await repo.delete_permanently(tenant_id, study_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Study not found")
    return None

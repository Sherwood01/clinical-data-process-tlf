"""Studies router — CRUD for clinical trial studies."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.study import StudyCreate, StudyResponse, StudyUpdate
from backend.db.repository.study_repo import StudyRepository
from backend.db.session import get_db

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
        description=study.description,
        status=study.status,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Study not found")
    return updated


@router.delete("/{study_id}", status_code=204)
async def archive_study(
    study_id: UUID,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Archive (soft-delete) a study."""
    repo = StudyRepository(db)
    archived = await repo.archive(tenant_id, study_id)
    if not archived:
        raise HTTPException(status_code=404, detail="Study not found")
    return None

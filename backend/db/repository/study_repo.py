"""Study repository — CRUD operations for clinical trial studies."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Study


class StudyRepository:
    """Data access layer for Study model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_tenant(self, tenant_id: UUID) -> List[Study]:
        result = await self.session.execute(
            select(Study)
            .where(Study.tenant_id == tenant_id)
            .order_by(Study.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, tenant_id: UUID, study_id: UUID) -> Optional[Study]:
        result = await self.session.execute(
            select(Study).where(Study.id == study_id, Study.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, tenant_id: UUID, name: str, protocol_id: Optional[str] = None,
        description: Optional[str] = None, created_by: Optional[UUID] = None,
    ) -> Study:
        study = Study(
            tenant_id=tenant_id,
            name=name,
            protocol_id=protocol_id,
            description=description,
            created_by=created_by,
        )
        self.session.add(study)
        await self.session.commit()
        await self.session.refresh(study)
        return study

    async def update(
        self, tenant_id: UUID, study_id: UUID,
        name: Optional[str] = None, protocol_id: Optional[str] = None,
        description: Optional[str] = None, status: Optional[str] = None,
    ) -> Optional[Study]:
        values = {}
        if name is not None:
            values["name"] = name
        if protocol_id is not None:
            values["protocol_id"] = protocol_id
        if description is not None:
            values["description"] = description
        if status is not None:
            values["status"] = status
        if not values:
            return await self.get_by_id(tenant_id, study_id)

        await self.session.execute(
            update(Study)
            .where(Study.id == study_id, Study.tenant_id == tenant_id)
            .values(**values)
        )
        await self.session.commit()
        return await self.get_by_id(tenant_id, study_id)

    async def archive(self, tenant_id: UUID, study_id: UUID) -> bool:
        result = await self.session.execute(
            update(Study)
            .where(Study.id == study_id, Study.tenant_id == tenant_id)
            .values(status="archived")
        )
        await self.session.commit()
        return result.rowcount > 0

    async def delete_permanently(self, tenant_id: UUID, study_id: UUID) -> bool:
        result = await self.session.execute(
            delete(Study).where(Study.id == study_id, Study.tenant_id == tenant_id)
        )
        await self.session.commit()
        return result.rowcount > 0

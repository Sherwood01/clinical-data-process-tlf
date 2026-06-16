import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from backend.db.models import TLFJob
from backend.core.config import settings
from backend.workers.celery_app import celery_app

async def run():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        res = await db.execute(select(TLFJob).order_by(TLFJob.created_at.desc()).limit(1))
        job = res.scalar_one_or_none()
        if job:
            print(f"Submitting job {job.id}")
            celery_app.send_task(
                "tlf.generate",
                args=[str(job.study_id), str(job.toc_entry_id), str(job.id), str(job.tenant_id)],
                task_id=str(job.id),
            )

asyncio.run(run())

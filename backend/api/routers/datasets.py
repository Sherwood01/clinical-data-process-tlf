"""Dataset management router."""
import hashlib
import os
import tempfile
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.dataset import (
    DatasetResponse,
    DatasetUploadStartRequest,
    DatasetUploadStartResponse,
    DatasetUploadCompleteRequest,
)
from backend.db.models import Dataset
from backend.db.session import get_db
from backend.storage.minio_client import storage

router = APIRouter(prefix="/studies/{study_id}/datasets")


async def get_tenant_id(request: Request) -> UUID:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant not identified")
    return UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    study_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """List all datasets for a study."""
    result = await db.execute(
        select(Dataset).where(
            Dataset.study_id == study_id,
            Dataset.tenant_id == tenant_id,
        )
    )
    return list(result.scalars().all())


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    study_id: UUID,
    dataset_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get dataset details."""
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.study_id == study_id,
            Dataset.tenant_id == tenant_id,
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post("/upload-start", response_model=DatasetUploadStartResponse)
async def start_dataset_upload(
    study_id: UUID,
    req: DatasetUploadStartRequest,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Step 1: Get a presigned URL for direct upload to MinIO."""
    suffix = ".sas7bdat"
    if req.filename:
        suffix = os.path.splitext(req.filename)[1] or ".sas7bdat"
    filename = f"{req.name}{suffix}"
    upload_url = await storage.get_presigned_upload_url(
        tenant_id=str(tenant_id),
        study_id=str(study_id),
        resource="datasets",
        filename=filename,
    )
    object_key = storage._object_key(str(study_id), "datasets", filename)
    return DatasetUploadStartResponse(upload_url=upload_url, object_key=object_key)


@router.post("/upload-complete", response_model=DatasetResponse, status_code=201)
async def complete_dataset_upload(
    study_id: UUID,
    req: DatasetUploadCompleteRequest,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Step 2: After client uploads to MinIO, extract metadata and create record."""
    bucket = storage._bucket_name(str(tenant_id))

    # Download file from MinIO to a temp file
    data = await storage.download_file(str(tenant_id), req.object_key)
    checksum = hashlib.sha256(data).hexdigest()

    suffix = (os.path.splitext(req.original_filename)[1] or ".sas7bdat").lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        # 根据后缀自适应选择读取方法
        if suffix == ".csv":
            import pandas as pd
            df = pd.read_csv(tmp_path)
            class DummyMeta:
                column_names = list(df.columns)
                column_labels = [None] * len(df.columns)
                number_rows = len(df)
                number_columns = len(df.columns)
            meta = DummyMeta()
        elif suffix in (".xpt", ".xport"):
            import pyreadstat
            df, meta = pyreadstat.read_xport(tmp_path)
        else:
            import pyreadstat
            df, meta = pyreadstat.read_sas7bdat(tmp_path)

        variables = []
        for i, name in enumerate(meta.column_names):
            col_type = str(df[name].dtype) if name in df.columns else "unknown"
            label = meta.column_labels[i] if meta.column_labels and i < len(meta.column_labels) else None
            variables.append({
                "name": name,
                "type": col_type,
                "label": label,
            })

        file_size = len(data)
        dataset = Dataset(
            study_id=study_id,
            tenant_id=tenant_id,
            name=req.name,
            original_filename=req.original_filename,
            file_format=suffix.lstrip("."),
            file_size_bytes=file_size,
            minio_bucket=bucket,
            minio_object_key=req.object_key,
            record_count=meta.number_rows,
            column_count=meta.number_columns,
            variables=variables,
            variable_names=list(meta.column_names),
            checksum_sha256=checksum,
        )
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        return dataset

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read dataset: {str(exc)}")
    finally:
        os.unlink(tmp_path)

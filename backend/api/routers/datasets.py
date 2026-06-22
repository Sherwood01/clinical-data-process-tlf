"""Dataset management router."""
import hashlib
import io
import os
import tempfile
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
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
from backend.storage import storage

router = APIRouter(prefix="/studies/{study_id}/datasets")


async def get_tenant_id(request: Request) -> UUID:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant not identified")
    return UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id


def _read_dataset_metadata(file_path: str, suffix: str):
    """Read a dataset file and extract metadata (variables, row count, etc.)."""
    if suffix == ".csv":
        import pandas as pd
        df = pd.read_csv(file_path)

        class DummyMeta:
            column_names = list(df.columns)
            column_labels = [None] * len(df.columns)
            number_rows = len(df)
            number_columns = len(df.columns)
        meta = DummyMeta()
    elif suffix in (".xpt", ".xport"):
        import pyreadstat
        df, meta = pyreadstat.read_xport(file_path)
    else:
        import pyreadstat
        df, meta = pyreadstat.read_sas7bdat(file_path)

    variables = []
    for i, name in enumerate(meta.column_names):
        col_type = str(df[name].dtype) if name in df.columns else "unknown"
        label = meta.column_labels[i] if meta.column_labels and i < len(meta.column_labels) else None
        variables.append({
            "name": name,
            "type": col_type,
            "label": label,
        })

    return variables, meta.column_names, meta.number_rows, meta.number_columns


@router.post("/upload-file", response_model=DatasetResponse, status_code=201)
async def upload_dataset_file(
    study_id: UUID,
    file: UploadFile = File(...),
    name: str = "",
    request: Request = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload dataset through API proxy (no presigned URL needed).

    The browser POSTs the file directly to this endpoint, which uploads
    to GCS via the Python SDK and extracts dataset metadata.
    """
    content = await file.read()
    filename = file.filename or "dataset.sas7bdat"

    # Infer dataset name from filename if not provided
    ds_name = name or os.path.splitext(filename)[0].lower()

    # Check and delete existing dataset with the same name (Replace)
    existing_query = await db.execute(
        select(Dataset).where(
            Dataset.study_id == study_id,
            Dataset.tenant_id == tenant_id,
            Dataset.name == ds_name
        )
    )
    existing = existing_query.scalar_one_or_none()
    if existing:
        if existing.minio_object_key:
            try:
                await storage.delete_file(str(tenant_id), existing.minio_object_key)
            except Exception as e:
                print(f"Failed to delete old file: {e}")
        await db.delete(existing)
        await db.commit()

    # Upload to GCS via SDK
    data_stream = io.BytesIO(content)
    object_key = storage.upload_file_sync(
        tenant_id=str(tenant_id),
        study_id=str(study_id),
        resource="datasets",
        filename=filename,
        data=data_stream,
        length=len(content),
        content_type=file.content_type or "application/octet-stream",
    )

    # Read metadata from temp file
    suffix = os.path.splitext(filename)[1].lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        variables, column_names, num_rows, num_cols = _read_dataset_metadata(tmp_path, suffix)

        file_size = len(content)
        dataset = Dataset(
            study_id=study_id,
            tenant_id=tenant_id,
            name=ds_name,
            original_filename=filename,
            file_format=suffix.lstrip("."),
            file_size_bytes=file_size,
            minio_bucket=storage._bucket_name(str(tenant_id)),
            minio_object_key=object_key,
            record_count=num_rows,
            column_count=num_cols,
            variables=variables,
            variable_names=list(column_names) if column_names else [],
            checksum_sha256=hashlib.sha256(content).hexdigest(),
        )
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        return dataset
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read dataset: {str(exc)}")
    finally:
        os.unlink(tmp_path)


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

    # Check and delete existing dataset with the same name (Replace)
    existing_query = await db.execute(
        select(Dataset).where(
            Dataset.study_id == study_id,
            Dataset.tenant_id == tenant_id,
            Dataset.name == req.name
        )
    )
    existing = existing_query.scalar_one_or_none()
    if existing:
        if existing.minio_object_key and existing.minio_object_key != req.object_key:
            try:
                await storage.delete_file(str(tenant_id), existing.minio_object_key)
            except Exception as e:
                print(f"Failed to delete old file: {e}")
        await db.delete(existing)
        await db.commit()

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


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    study_id: UUID,
    dataset_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a dataset and its source file from cloud storage."""
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.study_id == study_id,
            Dataset.tenant_id == tenant_id
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.minio_object_key:
        try:
            await storage.delete_file(str(tenant_id), dataset.minio_object_key)
        except Exception as e:
            print(f"Failed to delete file from storage: {e}")

    await db.delete(dataset)
    await db.commit()
    return None


@router.get("/{dataset_id}/preview")
async def preview_dataset(
    study_id: UUID,
    dataset_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get variables metadata and the first 50 rows of data in tabular format."""
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.study_id == study_id,
            Dataset.tenant_id == tenant_id
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not dataset.minio_object_key:
        raise HTTPException(status_code=400, detail="No source file found for this dataset")

    try:
        data = await storage.download_file(str(tenant_id), dataset.minio_object_key)
        suffix = f".{dataset.file_format}"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            import pandas as pd
            if suffix == ".csv":
                df = pd.read_csv(tmp_path)
            elif suffix in (".xpt", ".xport"):
                import pyreadstat
                df, _ = pyreadstat.read_xport(tmp_path)
            else:
                import pyreadstat
                df, _ = pyreadstat.read_sas7bdat(tmp_path)

            df_preview = df.head(50)
            records = []
            for row in df_preview.to_dict(orient="records"):
                clean_row = {}
                for k, v in row.items():
                    if pd.isna(v):
                        clean_row[k] = None
                    elif hasattr(v, "item"):
                        clean_row[k] = v.item()
                    else:
                        clean_row[k] = v
                    records.append(clean_row)

            return {
                "columns": list(df.columns),
                "data": records,
                "total_rows": len(df),
                "variables": dataset.variables
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to preview dataset: {str(e)}")

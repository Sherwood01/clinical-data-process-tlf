"""Pydantic schemas for Dataset API."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class DatasetUploadStartRequest(BaseModel):
    """Request to start a dataset upload: get a presigned URL."""
    name: str  # e.g. "adsl", "adae"


class DatasetUploadStartResponse(BaseModel):
    """Response with presigned URL for direct upload to MinIO."""
    upload_url: str
    object_key: str


class DatasetUploadCompleteRequest(BaseModel):
    """Notify the API that a dataset has been uploaded to MinIO."""
    name: str
    object_key: str
    original_filename: str


class DatasetResponse(BaseModel):
    id: UUID
    study_id: UUID
    name: str
    original_filename: Optional[str] = None
    file_format: Optional[str] = None
    file_size_bytes: Optional[int] = None
    record_count: Optional[int] = None
    column_count: Optional[int] = None
    variables: Optional[List[dict]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

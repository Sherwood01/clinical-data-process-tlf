"""Pydantic schemas for SAP document API."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SAPUploadStartResponse(BaseModel):
    """Response with presigned URL for direct upload to MinIO."""
    upload_url: str
    object_key: str


class SAPUploadCompleteRequest(BaseModel):
    """Notify the API that an SAP document has been uploaded."""
    object_key: str
    original_filename: str


class SAPDocumentResponse(BaseModel):
    id: UUID
    study_id: UUID
    original_filename: Optional[str] = None
    file_format: Optional[str] = None
    is_parsed: bool = False
    toc_entry_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TOCEntryResponse(BaseModel):
    id: UUID
    study_id: UUID
    tlf_id: str
    tlf_type: str
    tlf_name: Optional[str] = None
    population: Optional[str] = None
    sort_order: Optional[int] = None
    analysis_type: Optional[str] = None
    is_generated: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

"""Pydantic schemas for TLF generation API."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TLFGenerateRequest(BaseModel):
    toc_entry_id: Optional[UUID] = None
    tlf_id: Optional[str] = None
    tlf_type: Optional[str] = "table"
    tlf_name: Optional[str] = None


class TLFOutputResponse(BaseModel):
    id: UUID
    file_type: str
    minio_object_key: str
    file_size_bytes: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TLFJobResponse(BaseModel):
    id: UUID
    study_id: UUID
    toc_entry_id: Optional[UUID] = None
    tlf_id: str
    tlf_type: str
    tlf_name: Optional[str] = None
    status: str = "pending"
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tlf_outputs: List[TLFOutputResponse] = Field(default=[], validation_alias="outputs")

    class Config:
        from_attributes = True

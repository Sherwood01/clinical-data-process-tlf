"""SAP document management router."""
import os
import re
import tempfile
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.sap import (
    SAPDocumentResponse,
    SAPUploadStartResponse,
    SAPUploadCompleteRequest,
    TOCEntryResponse,
)
from backend.db.models import SAPDocument, TOCEntry
from backend.db.session import get_db
from backend.storage.minio_client import storage

router = APIRouter(prefix="/studies/{study_id}/sap")


async def get_tenant_id(request: Request) -> UUID:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant not identified")
    return UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id


# TLF ID prefix → analysis_type mapping
ANALYSIS_TYPE_PREFIX_MAP = {
    "14.1.1": "disposition",
    "14.1.2": "demographics",
    "14.1.3": "demographics",
    "14.1.4": "demographics",
    "14.2": "efficacy",
    "14.3": "ae_summary",
    "14.4": "laboratory",
    "14.5": "vital_signs",
}


def infer_analysis_type(tlf_id: str) -> str:
    """Infer analysis type from TLF ID prefix."""
    # tlf_id comes as "Table 14.1.1.1" — strip the type prefix
    clean_id = re.sub(r"^(Table|Figure|Listing)\s+", "", tlf_id)
    for prefix, atype in ANALYSIS_TYPE_PREFIX_MAP.items():
        if clean_id.startswith(prefix):
            return atype
    return "generic"


def clean_tlf_type(raw_type: str) -> str:
    """Normalize TLF type to lowercase."""
    return raw_type.lower().strip()


def clean_tlf_id(raw_id: str) -> str:
    """Extract just the ID number from 'Table 14.1.1.1'."""
    match = re.match(r"(?:Table|Figure|Listing)\s+([\d.]+)", raw_id)
    if match:
        return match.group(1)
    return raw_id


@router.get("", response_model=List[SAPDocumentResponse])
async def list_sap_documents(
    study_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """List SAP documents for a study."""
    result = await db.execute(
        select(SAPDocument).where(
            SAPDocument.study_id == study_id,
            SAPDocument.tenant_id == tenant_id,
        )
    )
    docs = list(result.scalars().all())
    # Augment with TOC entry count
    responses = []
    for doc in docs:
        responses.append(SAPDocumentResponse(
            id=doc.id,
            study_id=doc.study_id,
            original_filename=doc.original_filename,
            file_format=doc.file_format,
            is_parsed=doc.is_parsed,
            toc_entry_count=len(doc.toc_entries) if doc.toc_entries else 0,
            created_at=doc.created_at,
        ))
    return responses


@router.post("/upload-start", response_model=SAPUploadStartResponse)
async def start_sap_upload(
    study_id: UUID,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Step 1: Get a presigned URL for direct SAP upload to MinIO."""
    filename = "sap.docx"
    upload_url = await storage.get_presigned_upload_url(
        tenant_id=str(tenant_id),
        study_id=str(study_id),
        resource="sap",
        filename=filename,
    )
    object_key = storage._object_key(str(study_id), "sap", filename)
    return SAPUploadStartResponse(upload_url=upload_url, object_key=object_key)


@router.post("/upload-complete", response_model=SAPDocumentResponse, status_code=201)
async def complete_sap_upload(
    study_id: UUID,
    req: SAPUploadCompleteRequest,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Step 2: After upload, download from MinIO, parse TOC, store entries."""
    # Download SAP from MinIO to temp file
    data = await storage.download_file(str(tenant_id), req.object_key)
    suffix = os.path.splitext(req.original_filename)[1] or ".docx"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        sap_path = tmp.name

    try:
        # Parse SAP with existing TOC generator
        from src.report.toc_generator import SAPReader, TLFExtractor

        reader = SAPReader(sap_path)
        sap_text = reader.extract_full_text()

        extractor = TLFExtractor(sap_text)
        raw_entries = extractor.extract_all()

        # Create SAP document record
        file_format = suffix.lstrip(".")  # docx or pdf
        sap_doc = SAPDocument(
            study_id=study_id,
            tenant_id=tenant_id,
            original_filename=req.original_filename,
            file_format=file_format,
            minio_object_key=req.object_key,
            parsed_text=sap_text[:100000],  # Truncate to 100k chars for storage
            is_parsed=True,
        )
        db.add(sap_doc)
        await db.flush()  # Get sap_doc.id without committing

        # Create TOC entries
        toc_entries = []
        for idx, entry in enumerate(raw_entries):
            toc_entries.append(TOCEntry(
                study_id=study_id,
                tenant_id=tenant_id,
                sap_id=sap_doc.id,
                tlf_id=clean_tlf_id(entry["tlf_id"]),
                tlf_type=clean_tlf_type(entry["tlf_type"]),
                tlf_name=entry.get("tlf_name", ""),
                population=entry.get("population", ""),
                sort_order=idx,
                analysis_type=infer_analysis_type(entry["tlf_id"]),
            ))

        if toc_entries:
            db.add_all(toc_entries)

        await db.commit()
        await db.refresh(sap_doc)

        return SAPDocumentResponse(
            id=sap_doc.id,
            study_id=sap_doc.study_id,
            original_filename=sap_doc.original_filename,
            file_format=sap_doc.file_format,
            is_parsed=sap_doc.is_parsed,
            toc_entry_count=len(toc_entries),
            created_at=sap_doc.created_at,
        )

    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"TOC generator not available: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse SAP document: {str(exc)}",
        )
    finally:
        os.unlink(sap_path)


@router.get("/toc", response_model=List[TOCEntryResponse])
async def list_toc_entries(
    study_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """List parsed TOC entries for a study."""
    result = await db.execute(
        select(TOCEntry).where(
            TOCEntry.study_id == study_id,
            TOCEntry.tenant_id == tenant_id,
        ).order_by(TOCEntry.sort_order)
    )
    return list(result.scalars().all())

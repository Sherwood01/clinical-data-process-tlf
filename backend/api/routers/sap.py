"""SAP document management router."""
import io
import os
import re
import tempfile
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.schemas.sap import (
    SAPDocumentResponse,
    SAPUploadStartResponse,
    SAPUploadCompleteRequest,
    TOCEntryResponse,
    SAPDocumentUpdateRequest,
    TOCEntryUpdateRequest,
)
from backend.db.models import SAPDocument, TOCEntry, TLFJob
from backend.db.session import get_db
from backend.storage import storage
from backend.api.routers.studies import check_study_active

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
        select(SAPDocument)
        .options(selectinload(SAPDocument.toc_entries))
        .where(
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


@router.post("/upload-file", response_model=SAPDocumentResponse, status_code=201)
async def upload_sap_file(
    study_id: UUID,
    file: UploadFile = File(...),
    request: Request = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload SAP file through API proxy (no presigned URL needed)."""
    await check_study_active(study_id, tenant_id, db)
    content = await file.read()
    filename = file.filename or "sap.docx"

    # 检查是否存在同名文档
    result = await db.execute(
        select(SAPDocument).where(
            SAPDocument.study_id == study_id,
            SAPDocument.tenant_id == tenant_id,
            SAPDocument.original_filename == filename,
        )
    )
    existing_docs = result.scalars().all()
    if existing_docs:
        existing_doc_ids = [doc.id for doc in existing_docs]
        
        # 删除与这些已有文档对应的TOC条目关联的所有TLFJobs
        await db.execute(
            delete(TLFJob).where(
                TLFJob.toc_entry_id.in_(
                    select(TOCEntry.id).where(TOCEntry.sap_id.in_(existing_doc_ids))
                )
            )
        )
        # 删除关联的TOC条目
        await db.execute(
            delete(TOCEntry).where(
                TOCEntry.sap_id.in_(existing_doc_ids),
                TOCEntry.study_id == study_id,
                TOCEntry.tenant_id == tenant_id,
            )
        )
        # 删除旧文档实体以及对应的MinIO对象
        for doc in existing_docs:
            await db.delete(doc)
            new_object_key = storage._object_key(str(study_id), "sap", filename)
            if doc.minio_object_key and doc.minio_object_key != new_object_key:
                try:
                    await storage.delete_file(str(tenant_id), doc.minio_object_key)
                except Exception as exc:
                    print(f"Failed to delete old file from MinIO: {exc}")
        await db.flush()

    # Upload to MinIO directly via SDK (no browser-accessible URL needed)
    data_stream = io.BytesIO(content)
    object_key = storage.upload_file_sync(
        tenant_id=str(tenant_id),
        study_id=str(study_id),
        resource="sap",
        filename=filename,
        data=data_stream,
        length=len(content),
        content_type=file.content_type or "application/octet-stream",
    )

    # Parse SAP from temp file (reuse existing logic)
    suffix = os.path.splitext(filename)[1] or ".docx"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        sap_path = tmp.name

    try:
        from src.report.toc_generator import SAPReader, TLFExtractor, ICH3TLFInferencer

        reader = SAPReader(sap_path)
        sap_text = reader.extract_full_text()

        extractor = TLFExtractor(sap_text)
        raw_entries = extractor.extract_all()

        # Fallback to standard-based inference if explicit matches are 0
        if not raw_entries:
            inferencer = ICH3TLFInferencer(sap_text)
            raw_entries = inferencer.infer_tlf_ids()

        file_format = suffix.lstrip(".")
        sap_doc = SAPDocument(
            study_id=study_id,
            tenant_id=tenant_id,
            original_filename=filename,
            file_format=file_format,
            minio_object_key=object_key,
            parsed_text=sap_text[:100000],
            is_parsed=True,
        )
        db.add(sap_doc)
        await db.flush()

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
            minio_object_key=sap_doc.minio_object_key,
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


@router.post("/upload-start", response_model=SAPUploadStartResponse)
async def start_sap_upload(
    study_id: UUID,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Step 1: Get a presigned URL for direct SAP upload to MinIO."""
    await check_study_active(study_id, tenant_id, db)
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
    await check_study_active(study_id, tenant_id, db)
    # Download SAP from MinIO to temp file
    data = await storage.download_file(str(tenant_id), req.object_key)
    suffix = os.path.splitext(req.original_filename)[1] or ".docx"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        sap_path = tmp.name

    try:
        # Parse SAP with existing TOC generator
        from src.report.toc_generator import SAPReader, TLFExtractor, ICH3TLFInferencer

        reader = SAPReader(sap_path)
        sap_text = reader.extract_full_text()

        extractor = TLFExtractor(sap_text)
        raw_entries = extractor.extract_all()

        # Fallback to standard-based inference if explicit matches are 0
        if not raw_entries:
            inferencer = ICH3TLFInferencer(sap_text)
            raw_entries = inferencer.infer_tlf_ids()

        # 检查是否存在同名文档
        result = await db.execute(
            select(SAPDocument).where(
                SAPDocument.study_id == study_id,
                SAPDocument.tenant_id == tenant_id,
                SAPDocument.original_filename == req.original_filename,
            )
        )
        existing_docs = result.scalars().all()
        if existing_docs:
            existing_doc_ids = [doc.id for doc in existing_docs]
            
            # 删除与这些已有文档对应的TOC条目关联的所有TLFJobs
            await db.execute(
                delete(TLFJob).where(
                    TLFJob.toc_entry_id.in_(
                        select(TOCEntry.id).where(TOCEntry.sap_id.in_(existing_doc_ids))
                    )
                )
            )
            # 删除关联的TOC条目
            await db.execute(
                delete(TOCEntry).where(
                    TOCEntry.sap_id.in_(existing_doc_ids),
                    TOCEntry.study_id == study_id,
                    TOCEntry.tenant_id == tenant_id,
                )
            )
            # 删除旧文档实体以及对应的MinIO对象
            for doc in existing_docs:
                await db.delete(doc)
                if doc.minio_object_key and doc.minio_object_key != req.object_key:
                    try:
                        await storage.delete_file(str(tenant_id), doc.minio_object_key)
                    except Exception as exc:
                        print(f"Failed to delete old file from MinIO: {exc}")
            await db.flush()

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
            minio_object_key=sap_doc.minio_object_key,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse SAP document: {str(exc)}",
        )
    finally:
        os.unlink(sap_path)


@router.get("/{sap_id}/download")
async def download_sap_document(
    study_id: UUID,
    sap_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a presigned download URL for an SAP document."""
    result = await db.execute(
        select(SAPDocument).where(
            SAPDocument.id == sap_id,
            SAPDocument.study_id == study_id,
            SAPDocument.tenant_id == tenant_id,
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="SAP document not found")

    try:
        url = await storage.get_presigned_download_url(str(tenant_id), doc.minio_object_key)
        return {"download_url": url}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate download URL: {str(exc)}",
        )


@router.get("/{sap_id}/file")
async def get_sap_document_file(
    study_id: UUID,
    sap_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """直接流式返回 SAP 文档的二进制内容，绕过前端跨域限制。

    参数:
        study_id: 项目ID
        sap_id: SAP文档ID
        tenant_id: 租户ID
        db: 数据库异步会话
    """
    result = await db.execute(
        select(SAPDocument).where(
            SAPDocument.id == sap_id,
            SAPDocument.study_id == study_id,
            SAPDocument.tenant_id == tenant_id,
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="SAP document not found")

    try:
        content = await storage.download_file(str(tenant_id), doc.minio_object_key)
        filename = doc.original_filename or "document.docx"
        content_type = "application/octet-stream"
        if filename.lower().endswith(".docx"):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif filename.lower().endswith(".pdf"):
            content_type = "application/pdf"

        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"'
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch document content: {str(exc)}",
        )



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


@router.delete("/{sap_id}", status_code=204)
async def delete_sap_document(
    study_id: UUID,
    sap_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete an SAP document, its parsed TOC entries, and its file in MinIO."""
    await check_study_active(study_id, tenant_id, db)
    result = await db.execute(
        select(SAPDocument).where(
            SAPDocument.id == sap_id,
            SAPDocument.study_id == study_id,
            SAPDocument.tenant_id == tenant_id,
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="SAP document not found")

    try:
        # Delete file in MinIO
        if doc.minio_object_key:
            await storage.delete_file(str(tenant_id), doc.minio_object_key)
    except Exception as exc:
        print(f"Failed to delete file from MinIO: {exc}")

    # Delete associated TLF jobs first to avoid foreign key violations
    await db.execute(
        delete(TLFJob).where(
            TLFJob.toc_entry_id.in_(
                select(TOCEntry.id).where(
                    TOCEntry.sap_id == sap_id,
                    TOCEntry.study_id == study_id,
                    TOCEntry.tenant_id == tenant_id
                )
            )
        )
    )

    # Delete associated TOC entries
    await db.execute(
        delete(TOCEntry).where(
            TOCEntry.sap_id == sap_id,
            TOCEntry.study_id == study_id,
            TOCEntry.tenant_id == tenant_id,
        )
    )

    # Delete SAP document record
    await db.delete(doc)
    await db.commit()
    return


@router.patch("/{sap_id}", response_model=SAPDocumentResponse)
async def update_sap_document(
    study_id: UUID,
    sap_id: UUID,
    req: SAPDocumentUpdateRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    await check_study_active(study_id, tenant_id, db)
    """Rename an SAP document."""
    result = await db.execute(
        select(SAPDocument)
        .options(selectinload(SAPDocument.toc_entries))
        .where(
            SAPDocument.id == sap_id,
            SAPDocument.study_id == study_id,
            SAPDocument.tenant_id == tenant_id,
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="SAP document not found")

    doc.original_filename = req.original_filename
    await db.commit()
    await db.refresh(doc)
    
    return SAPDocumentResponse(
        id=doc.id,
        study_id=doc.study_id,
        original_filename=doc.original_filename,
        file_format=doc.file_format,
        is_parsed=doc.is_parsed,
        toc_entry_count=len(doc.toc_entries) if doc.toc_entries else 0,
        created_at=doc.created_at,
        minio_object_key=doc.minio_object_key,
    )


@router.get("/{sap_id}/preview")
async def preview_sap_document(
    study_id: UUID,
    sap_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the extracted parsed text of an SAP document for previewing."""
    result = await db.execute(
        select(SAPDocument).where(
            SAPDocument.id == sap_id,
            SAPDocument.study_id == study_id,
            SAPDocument.tenant_id == tenant_id,
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="SAP document not found")

    return {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "parsed_text": doc.parsed_text,
    }


@router.patch("/toc/{entry_id}", response_model=TOCEntryResponse)
async def update_toc_entry(
    study_id: UUID,
    entry_id: UUID,
    req: TOCEntryUpdateRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    await check_study_active(study_id, tenant_id, db)
    """Update a specific parsed TOC entry's properties."""
    result = await db.execute(
        select(TOCEntry).where(
            TOCEntry.id == entry_id,
            TOCEntry.study_id == study_id,
            TOCEntry.tenant_id == tenant_id,
        )
    )
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=404, detail="TOC entry not found")

    if req.tlf_id is not None:
        entry.tlf_id = req.tlf_id
        entry.analysis_type = infer_analysis_type(req.tlf_id)
    if req.tlf_type is not None:
        entry.tlf_type = clean_tlf_type(req.tlf_type)
    if req.tlf_name is not None:
        entry.tlf_name = req.tlf_name
    if req.population is not None:
        entry.population = req.population
    if req.analysis_type is not None:
        entry.analysis_type = req.analysis_type

    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/toc/{entry_id}", status_code=204)
async def delete_toc_entry(
    study_id: UUID,
    entry_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    await check_study_active(study_id, tenant_id, db)
    """Delete a specific TOC entry."""
    result = await db.execute(
        select(TOCEntry).where(
            TOCEntry.id == entry_id,
            TOCEntry.study_id == study_id,
            TOCEntry.tenant_id == tenant_id,
        )
    )
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=404, detail="TOC entry not found")

    await db.delete(entry)
    await db.commit()
    return

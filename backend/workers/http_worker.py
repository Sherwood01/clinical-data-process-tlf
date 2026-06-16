"""HTTP Worker for TLF report generation.

Replaces Celery for Cloud Run deployments. This is a standalone FastAPI
app that receives TLF generation requests and executes them synchronously.
"""
import logging
import os
import sys
import tempfile
import io
from datetime import datetime
from pathlib import Path
from uuid import UUID

if "/app" not in sys.path:
    sys.path.insert(0, "/app")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.core.config import settings

# Sync DB engine
_sync_engine = None


def _get_sync_db():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(settings.DATABASE_SYNC_URL)
    return Session(_sync_engine)


app = FastAPI(title="TLF Worker", version="0.1.0")
logger = logging.getLogger("tlf-http-worker")


class TLFGenerateRequest(BaseModel):
    study_id: str
    toc_entry_id: str
    job_id: str
    tenant_id: str


@app.on_event("startup")
async def startup():
    logging.basicConfig(level=logging.INFO)


@app.post("/tlf/generate")
async def generate_tlf(req: TLFGenerateRequest):
    """Execute a TLF generation job synchronously."""
    logger.info(f"Received TLF generation request: job={req.job_id} entry={req.toc_entry_id}")

    from backend.db.models import Study, TOCEntry, TLFJob, TLFOutput, Dataset
    from backend.services.analysis.models import AnalysisConfig
    from backend.services.analysis.pipeline import (
        get_analyzer,
        get_required_datasets,
        infer_analysis_type,
        is_figure_type,
        is_listing_type,
    )
    from backend.services.pdf.generator import PDFGenerator
    from backend.storage import storage

    db = _get_sync_db()

    try:
        # 1. Load TOC entry
        toc_entry = db.query(TOCEntry).filter(TOCEntry.id == req.toc_entry_id).first()
        if not toc_entry:
            raise ValueError(f"TOC entry not found: {req.toc_entry_id}")

        study = db.query(Study).filter(Study.id == req.study_id).first()
        if not study:
            raise ValueError(f"Study not found: {req.study_id}")

        # 2. Determine analysis type
        analysis_type = infer_analysis_type(toc_entry.tlf_id, toc_entry.tlf_type)
        if analysis_type == "generic":
            analysis_type = toc_entry.analysis_type or "generic"

        required_datasets = get_required_datasets(analysis_type)
        logger.info(f"Generating '{toc_entry.tlf_id}' type={toc_entry.tlf_type}, analysis={analysis_type}")

        # Update job status
        job = db.query(TLFJob).filter(TLFJob.id == req.job_id).first()
        if job:
            job.status = "running"
            job.started_at = datetime.utcnow()
            db.commit()

        # 3. Download datasets
        datasets = {}
        dataset_records = (
            db.query(Dataset)
            .filter(
                Dataset.study_id == req.study_id,
                Dataset.tenant_id == req.tenant_id,
                Dataset.name.in_(required_datasets),
            )
            .all()
        )

        name_map = {r.name: r for r in dataset_records}
        for ds_name in required_datasets:
            record = name_map.get(ds_name)
            if not record:
                logger.warning(f"Dataset '{ds_name}' not found, using empty DataFrame")
                import pandas as pd
                datasets[ds_name] = pd.DataFrame()
                continue

            data = storage.download_file_sync(req.tenant_id, record.minio_object_key)
            with tempfile.NamedTemporaryFile(suffix=".sas7bdat", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                import pyreadstat
                df, _ = pyreadstat.read_sas7bdat(tmp_path)
                datasets[ds_name] = df
                logger.info(f"Loaded '{ds_name}': {len(df)} rows, {len(df.columns)} cols")
            except Exception as e:
                logger.error(f"Failed to read '{ds_name}': {e}")
                import pandas as pd
                datasets[ds_name] = pd.DataFrame()
            finally:
                os.unlink(tmp_path)

        # 4. Generate output
        temp_dir = Path(settings.WORKER_TEMP_DIR)
        os.makedirs(temp_dir, exist_ok=True)

        pdf_filename = f"{toc_entry.tlf_id}_{req.job_id}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)

        if is_listing_type(analysis_type):
            from backend.services.listings.generator import ListingConfig, generate_listing_pdf
            listing_config = ListingConfig(
                listing_id=toc_entry.tlf_id,
                population=toc_entry.population or "Enrolled Analysis Set",
            )
            generate_listing_pdf(datasets, listing_config, pdf_path)

        elif is_figure_type(analysis_type):
            from backend.services.figures.generator import FigureConfig, generate_figure_pdf
            figure_config = FigureConfig(
                tlf_id=toc_entry.tlf_id,
                title=toc_entry.tlf_name or toc_entry.tlf_id,
                population=toc_entry.population or "",
                figure_type=analysis_type,
            )
            generate_figure_pdf(datasets, figure_config, pdf_path)

        else:
            config = AnalysisConfig(
                population_filter="enrolled",
                study_settings=study.settings or {},
            )
            analyzer = get_analyzer(analysis_type, datasets, config)
            table_data = analyzer.analyze()
            pdf_gen = PDFGenerator()
            pdf_gen.generate_table(table_data, pdf_path)

        # 5. Upload PDF to GCS
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        result_key = storage.upload_file_sync(
            tenant_id=req.tenant_id,
            study_id=req.study_id,
            resource="tlf",
            filename=pdf_filename,
            data=io.BytesIO(pdf_data),
            length=len(pdf_data),
            content_type="application/pdf",
        )

        # 6. Create TLFOutput record
        output = TLFOutput(
            job_id=req.job_id,
            study_id=req.study_id,
            tenant_id=req.tenant_id,
            file_type="pdf",
            minio_object_key=result_key,
            file_size_bytes=len(pdf_data),
        )
        db.add(output)

        # 7. Mark TOC entry as generated
        toc_entry.is_generated = True

        # 8. Update job as completed
        if job:
            job.status = "completed"
            job.progress = 1.0
            job.completed_at = datetime.utcnow()

        db.commit()
        os.unlink(pdf_path)

        return {
            "status": "completed",
            "object_key": result_key,
            "job_id": req.job_id,
        }

    except Exception as exc:
        logger.exception("TLF generation failed")
        try:
            job = db.query(TLFJob).filter(TLFJob.id == req.job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                db.commit()
        except Exception:
            pass
        finally:
            db.close()

        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

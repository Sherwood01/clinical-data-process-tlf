"""Celery task definitions for TLF report generation.

IMPORTANT: Celery workers run in synchronous mode. DB access uses sync SQLAlchemy
(via DATABASE_SYNC_URL), and MinIO client calls are invoked synchronously since
the underlying minio library is synchronous (the async wrappers are only needed
in the FastAPI async context).
"""
import logging
import os
import sys
if "/app" not in sys.path:
    sys.path.insert(0, "/app")
import tempfile
from datetime import datetime
from pathlib import Path

import pyreadstat
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.db.models import Dataset, Study, TOCEntry, TLFJob, TLFOutput
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
from backend.workers.celery_app import celery_app

logger = logging.getLogger("tlf-worker")

# Sync DB engine (Celery can't use async sessions)
_sync_engine = None


def _get_sync_db():
    """Get a synchronous DB session."""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(settings.DATABASE_SYNC_URL)
    return Session(_sync_engine)


def _progress_callback(task_self, progress: float, step: str):
    """Update Celery task state with progress."""
    task_self.update_state(
        state="RUNNING",
        meta={"progress": progress, "step": step},
    )


@celery_app.task(bind=True, name="tlf.generate")
def generate_tlf_report(self, study_id: str, toc_entry_id: str, job_id: str, tenant_id: str):
    """Generate a TLF report asynchronously.

    Runs the full pipeline synchronously inside the Celery worker:
    1. Load TOC entry + Study config from DB
    2. Download required ADaM datasets from MinIO
    3. Run statistical analysis via the pipeline
    4. Generate PDF output
    5. Upload results to MinIO
    6. Update job status in DB
    """
    self.update_state(state="RUNNING", meta={"progress": 0.0, "step": "Initializing"})
    db = _get_sync_db()

    try:
        # 1. Load TOC entry
        _progress_callback(self, 0.05, "Loading configuration")
        toc_entry = db.query(TOCEntry).filter(TOCEntry.id == toc_entry_id).first()
        if not toc_entry:
            raise ValueError(f"TOC entry not found: {toc_entry_id}")

        study = db.query(Study).filter(Study.id == study_id).first()
        if not study:
            raise ValueError(f"Study not found: {study_id}")

        # 2. Determine analysis type
        analysis_type = infer_analysis_type(toc_entry.tlf_id, toc_entry.tlf_type)
        if analysis_type == "generic":
            analysis_type = toc_entry.analysis_type or "generic"

        required_datasets = get_required_datasets(analysis_type)
        logger.info(f"Generating '{toc_entry.tlf_id}' type={toc_entry.tlf_type}, analysis={analysis_type}, datasets={required_datasets}")

        # Update job status in DB
        job = db.query(TLFJob).filter(TLFJob.id == job_id).first()
        if job:
            job.status = "running"
            job.started_at = datetime.utcnow()
            db.commit()

        # 3. Download datasets from MinIO
        _progress_callback(self, 0.2, "Downloading datasets")
        datasets = {}
        dataset_records = (
            db.query(Dataset)
            .filter(
                Dataset.study_id == study_id,
                Dataset.tenant_id == tenant_id,
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

            data = storage.download_file_sync(tenant_id, record.minio_object_key)
            with tempfile.NamedTemporaryFile(suffix=".sas7bdat", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                df, _ = pyreadstat.read_sas7bdat(tmp_path)
                datasets[ds_name] = df
                logger.info(f"Loaded '{ds_name}': {len(df)} rows, {len(df.columns)} cols")
            except Exception as e:
                logger.error(f"Failed to read '{ds_name}': {e}")
                import pandas as pd
                datasets[ds_name] = pd.DataFrame()
            finally:
                os.unlink(tmp_path)

        # 4. Generate output based on type
        _progress_callback(self, 0.5, "Generating output")
        temp_dir = Path(settings.WORKER_TEMP_DIR)
        os.makedirs(temp_dir, exist_ok=True)

        pdf_filename = f"{toc_entry.tlf_id}_{job_id}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)

        if is_listing_type(analysis_type):
            from backend.services.listings.generator import (
                ListingConfig,
                generate_listing_pdf,
            )
            listing_config = ListingConfig(
                listing_id=toc_entry.tlf_id,
                population=toc_entry.population or "Enrolled Analysis Set",
            )
            generate_listing_pdf(datasets, listing_config, pdf_path)

        elif is_figure_type(analysis_type):
            from backend.services.figures.generator import (
                FigureConfig,
                generate_figure_pdf,
            )
            figure_config = FigureConfig(
                tlf_id=toc_entry.tlf_id,
                title=toc_entry.tlf_name or toc_entry.tlf_id,
                population=toc_entry.population or "",
                figure_type=analysis_type,
            )
            generate_figure_pdf(datasets, figure_config, pdf_path)

        else:
            # Standard table analysis
            _progress_callback(self, 0.5, "Running analysis")
            config = AnalysisConfig(
                population_filter="enrolled",
                study_settings=study.settings or {},
            )
            analyzer = get_analyzer(analysis_type, datasets, config)
            table_data = analyzer.analyze()

            _progress_callback(self, 0.7, "Generating PDF")
            pdf_gen = PDFGenerator()
            pdf_gen.generate_table(table_data, pdf_path)

        # 6. Upload PDF to MinIO
        _progress_callback(self, 0.9, "Uploading results")

        import io
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        result_key = storage.upload_file_sync(
            tenant_id=tenant_id,
            study_id=study_id,
            resource="tlf",
            filename=pdf_filename,
            data=io.BytesIO(pdf_data),
            length=len(pdf_data),
            content_type="application/pdf",
        )

        # Clean up old completed jobs and output files for the same TOC entry
        try:
            old_jobs = (
                db.query(TLFJob)
                .filter(
                    TLFJob.study_id == study_id,
                    TLFJob.tenant_id == tenant_id,
                    TLFJob.toc_entry_id == toc_entry_id,
                    TLFJob.status == "completed",
                    TLFJob.id != job_id,
                )
                .all()
            )
            for old_job in old_jobs:
                old_outputs = db.query(TLFOutput).filter(TLFOutput.job_id == old_job.id).all()
                for old_output in old_outputs:
                    try:
                        storage.delete_file_sync(tenant_id, old_output.minio_object_key)
                    except Exception as e:
                        logger.error(f"Failed to delete old physical output file {old_output.minio_object_key}: {e}")
                    db.delete(old_output)
                db.delete(old_job)
            db.commit()
        except Exception as e:
            logger.error(f"Error during cleaning up old TLF reports: {e}")

        # 7. Create TLFOutput record
        output = TLFOutput(
            job_id=job_id,
            study_id=study_id,
            tenant_id=tenant_id,
            file_type="pdf",
            minio_object_key=result_key,
            file_size_bytes=len(pdf_data),
        )
        db.add(output)

        # 8. Mark TOC entry as generated
        toc_entry.is_generated = True

        # 9. Update job as completed
        if job:
            job.status = "completed"
            job.progress = 1.0
            job.completed_at = datetime.utcnow()

        db.commit()

        # Cleanup
        os.unlink(pdf_path)

        self.update_state(
            state="SUCCESS",
            meta={"progress": 1.0, "step": "Complete", "object_key": result_key},
        )
        return {"status": "completed", "object_key": result_key}

    except Exception as exc:
        logger.exception("TLF generation failed")
        self.update_state(state="FAILURE", meta={"error": str(exc)})

        # Update job as failed
        try:
            job = db.query(TLFJob).filter(TLFJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                db.commit()
        except Exception:
            pass
        finally:
            db.close()

        # Return failure instead of re-raising to avoid Celery serialization issues
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()

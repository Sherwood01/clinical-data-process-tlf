"""TLF orchestrator — coordinates the full report generation pipeline.

Flow:
  1. Load TOC entry + Study config from DB
  2. Determine output type (table / figure / listing)
  3. Download required ADaM datasets from MinIO
  4. Run analysis / generate figure / generate listing
  5. Generate PDF output
  6. Upload results to MinIO
  7. Create TLFOutput records
  8. Mark TOCEntry as generated
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

import pandas as pd

from backend.core.config import settings
from backend.services.analysis.models import AnalysisConfig
from backend.services.analysis.pipeline import (
    get_analyzer,
    get_required_datasets,
    infer_analysis_type,
    is_figure_type,
    is_listing_type,
)
from backend.services.pdf.generator import PDFGenerator
from backend.storage.minio_client import MinioStorage

logger = logging.getLogger("tlf-orchestrator")


class TLFOrchestrator:
    """Orchestrates the end-to-end TLF report generation pipeline."""

    def __init__(self, db_session, storage: MinioStorage, tenant_id: str):
        self.db = db_session
        self.storage = storage
        self.tenant_id = tenant_id
        self.temp_dir = Path(settings.WORKER_TEMP_DIR)

    def run(
        self,
        study_id: str,
        toc_entry_id: str,
        job_id: str,
        progress_callback=None,
    ) -> Dict:
        """Execute the full TLF generation pipeline synchronously.

        Args:
            study_id: UUID of the study.
            toc_entry_id: UUID of the TOC entry to generate.
            job_id: UUID of the TLFJob record.
            progress_callback: Optional callable(progress, step) for status updates.

        Returns:
            Dict with keys: status, object_key (MinIO key for the generated PDF).
        """
        # 1. Load TOC entry + Study
        if progress_callback:
            progress_callback(0.1, "Loading configuration")

        from backend.db.models import Study, TOCEntry

        toc_entry = self.db.query(TOCEntry).filter(TOCEntry.id == toc_entry_id).first()
        if not toc_entry:
            raise ValueError(f"TOC entry not found: {toc_entry_id}")

        study = self.db.query(Study).filter(Study.id == study_id).first()
        if not study:
            raise ValueError(f"Study not found: {study_id}")

        # 2. Determine analysis type and required datasets
        analysis_type = infer_analysis_type(toc_entry.tlf_id, toc_entry.tlf_type)
        if analysis_type == "generic":
            analysis_type = toc_entry.analysis_type or "generic"

        required = get_required_datasets(analysis_type)
        logger.info(
            f"TOC entry {toc_entry.tlf_id} type={toc_entry.tlf_type} "
            f"analysis_type={analysis_type}, datasets={required}"
        )

        # 3. Download datasets from MinIO
        if progress_callback:
            progress_callback(0.3, "Downloading datasets")

        datasets = self._download_datasets(study_id, required)

        # 4. Generate output based on type
        if progress_callback:
            progress_callback(0.5, "Generating output")

        os.makedirs(self.temp_dir, exist_ok=True)
        pdf_filename = f"{toc_entry.tlf_id}_{job_id}.pdf"
        pdf_path = os.path.join(self.temp_dir, pdf_filename)

        if is_listing_type(analysis_type):
            # Generate listing PDF
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
            # Generate figure PDF
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
            # Generate table PDF (standard analysis)
            config = AnalysisConfig(
                population_filter="enrolled",
                study_settings=study.settings or {},
            )
            analyzer = get_analyzer(analysis_type, datasets, config)
            table_data = analyzer.analyze()
            pdf_gen = PDFGenerator()
            pdf_gen.generate_table(table_data, pdf_path)

        # 6. Upload PDF to MinIO
        if progress_callback:
            progress_callback(0.9, "Uploading results")

        import io
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        result_key = self.storage.upload_file_sync(
            tenant_id=self.tenant_id,
            study_id=str(study_id),
            resource="tlf",
            filename=pdf_filename,
            data=io.BytesIO(pdf_data),
            length=len(pdf_data),
            content_type="application/pdf",
        )

        # 7. Update TOC entry as generated
        toc_entry.is_generated = True
        self.db.commit()

        # Cleanup temp file
        os.unlink(pdf_path)

        return {"status": "completed", "object_key": result_key}

    def _download_datasets(self, study_id: str, required: list) -> Dict[str, pd.DataFrame]:
        """Download required ADaM datasets from MinIO, return as dict of DataFrames."""
        import pyreadstat

        from backend.db.models import Dataset

        datasets = {}
        dataset_records = (
            self.db.query(Dataset)
            .filter(
                Dataset.study_id == study_id,
                Dataset.tenant_id == self.tenant_id,
                Dataset.name.in_(required),
            )
            .all()
        )

        name_map = {r.name: r for r in dataset_records}

        for ds_name in required:
            record = name_map.get(ds_name)
            if not record:
                logger.warning(f"Dataset '{ds_name}' not found for study {study_id}")
                datasets[ds_name] = pd.DataFrame()
                continue

            # Download from MinIO (sync method for Celery worker context)
            data = self.storage.download_file_sync(
                self.tenant_id, record.minio_object_key
            )

            with tempfile.NamedTemporaryFile(suffix=".sas7bdat", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                df, _ = pyreadstat.read_sas7bdat(tmp_path)
                datasets[ds_name] = df
                logger.info(f"Loaded dataset '{ds_name}': {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                logger.error(f"Failed to read dataset '{ds_name}': {e}")
                datasets[ds_name] = pd.DataFrame()
            finally:
                os.unlink(tmp_path)

        return datasets

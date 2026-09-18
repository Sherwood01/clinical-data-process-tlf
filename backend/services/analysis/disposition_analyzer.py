"""Wrapper for DispositionAnalyzer (Table 14.1.1.1)."""
from backend.services.analysis.base_analyzer import BaseAnalyzer
from backend.services.analysis.models import TableData


class DispositionAnalyzerWrapper(BaseAnalyzer):
    """Subject disposition analysis — wraps src.report.direct_generator.DispositionAnalyzer."""

    def analyze(self) -> TableData:
        import sys
        import os
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"SYS PATH INSIDE ANALYZE: {sys.path}")
        logger.error(f"Does /app/src exist? {os.path.exists('/app/src')}")
        logger.error(f"Files in /app/src: {os.listdir('/app/src') if os.path.exists('/app/src') else 'N/A'}")
        try:
            from src.report.direct_generator import DispositionAnalyzer
        except Exception as e:
            logger.error(f"IMPORT FAILED: {repr(e)}")
            raise
        adsl = self._get_adsl()
        inner = DispositionAnalyzer(adsl)
        result = inner.analyze()

        return self._result_to_tabledata(
            result,
            tlf_id="14.1.1.1",
            title="Subject Disposition",
            population="Enrolled Analysis Set",
            analysis_type="disposition",
            group_labels={1: "Arm 1", 2: "Arm 2", 3: "Arm 3"},
        )

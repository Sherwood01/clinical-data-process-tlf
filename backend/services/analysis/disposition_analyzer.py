"""Wrapper for DispositionAnalyzer (Table 14.1.1.1)."""
from backend.services.analysis.base_analyzer import BaseAnalyzer
from backend.services.analysis.models import TableData


class DispositionAnalyzerWrapper(BaseAnalyzer):
    """Subject disposition analysis — wraps src.report.direct_generator.DispositionAnalyzer."""

    def analyze(self) -> TableData:
        from src.report.direct_generator import DispositionAnalyzer

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

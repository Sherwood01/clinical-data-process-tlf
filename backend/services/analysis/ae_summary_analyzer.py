"""Wrapper for AESummaryAnalyzer (Table 14.3.1.x)."""
from backend.services.analysis.base_analyzer import BaseAnalyzer
from backend.services.analysis.models import TableData


class AESummaryAnalyzerWrapper(BaseAnalyzer):
    """Adverse event summary — wraps src.report.direct_generator.AESummaryAnalyzer."""

    def analyze(self) -> TableData:
        from src.report.direct_generator import AESummaryAnalyzer

        adsl = self._get_adsl()
        adae = self._get_adae()
        inner = AESummaryAnalyzer(adae, adsl)
        result = inner.analyze()

        return self._result_to_tabledata(
            result,
            tlf_id="14.3.1.1",
            title="Overall Summary of Adverse Events",
            population="Safety Analysis Set",
            analysis_type="ae_summary",
            group_labels={1: "Arm 1", 2: "Arm 2", 3: "Arm 3"},
        )

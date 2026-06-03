"""Wrapper for LaboratoryAnalyzer (Table 14.4.x)."""
from backend.services.analysis.base_analyzer import BaseAnalyzer
from backend.services.analysis.models import TableData


class LaboratoryAnalyzerWrapper(BaseAnalyzer):
    """Lab results analysis — wraps src.report.direct_generator.LaboratoryAnalyzer."""

    def analyze(self) -> TableData:
        from src.report.direct_generator import LaboratoryAnalyzer

        adsl = self._get_adsl()
        adlb = self._get_adlb()
        inner = LaboratoryAnalyzer(adlb, adsl)
        result = inner.analyze()

        return self._result_to_tabledata(
            result,
            tlf_id="14.4.1.1",
            title="Laboratory Results Summary",
            population="Safety Analysis Set",
            analysis_type="laboratory",
            group_labels={1: "Arm 1", 2: "Arm 2", 3: "Arm 3"},
        )

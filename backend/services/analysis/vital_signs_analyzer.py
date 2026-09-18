"""Wrapper for VitalSignsAnalyzer (Table 14.5.x)."""
from backend.services.analysis.base_analyzer import BaseAnalyzer
from backend.services.analysis.models import TableData


class VitalSignsAnalyzerWrapper(BaseAnalyzer):
    """Vital signs analysis — wraps src.report.direct_generator.VitalSignsAnalyzer."""

    def analyze(self) -> TableData:
        from src.report.direct_generator import VitalSignsAnalyzer

        adsl = self._get_adsl()
        advs = self._get_advs()
        inner = VitalSignsAnalyzer(advs, adsl)
        result = inner.analyze()

        return self._result_to_tabledata(
            result,
            tlf_id="14.5.1.1",
            title="Vital Signs Summary",
            population="Safety Analysis Set",
            analysis_type="vital_signs",
            group_labels={1: "Arm 1", 2: "Arm 2", 3: "Arm 3"},
        )

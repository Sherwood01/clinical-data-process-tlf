"""Wrapper for SurvivalAnalyzer / OverallSurvivalAnalyzer (KM curves)."""
from backend.services.analysis.base_analyzer import BaseAnalyzer
from backend.services.analysis.models import TableData


class SurvivalAnalyzerWrapper(BaseAnalyzer):
    """Survival analysis (PFS) — wraps src.report.direct_generator.SurvivalAnalyzer."""

    def analyze(self) -> TableData:
        from src.report.direct_generator import SurvivalAnalyzer

        adsl = self._get_adsl()
        adtte = self._get_adtte()
        inner = SurvivalAnalyzer(adtte, adsl)
        result = inner.analyze()

        return self._result_to_tabledata(
            result,
            tlf_id="14.2.1.1",
            title="Progression-Free Survival Analysis",
            population="Full Analysis Set",
            analysis_type="survival",
            group_labels={1: "Arm 1", 2: "Arm 2", 3: "Arm 3"},
        )


class OverallSurvivalAnalyzerWrapper(BaseAnalyzer):
    """Overall survival analysis — wraps src.report.direct_generator.OverallSurvivalAnalyzer."""

    def analyze(self) -> TableData:
        from src.report.direct_generator import OverallSurvivalAnalyzer

        adsl = self._get_adsl()
        adtte = self._get_adtte()
        inner = OverallSurvivalAnalyzer(adtte, adsl)
        result = inner.analyze()

        return self._result_to_tabledata(
            result,
            tlf_id="14.2.1.2",
            title="Overall Survival Analysis",
            population="Full Analysis Set",
            analysis_type="survival",
            group_labels={1: "Arm 1", 2: "Arm 2", 3: "Arm 3"},
        )

"""Wrapper for DemographicAnalyzer (Table 14.1.2.x)."""
from backend.services.analysis.base_analyzer import BaseAnalyzer
from backend.services.analysis.models import AnalysisConfig, TableData


class DemographicAnalyzerWrapper(BaseAnalyzer):
    """Demographics analysis — wraps src.report.direct_generator.DemographicAnalyzer."""

    def analyze(self) -> TableData:
        from src.report.direct_generator import DemographicAnalyzer

        adsl = self._get_adsl()
        pop_filter = getattr(self.config, "population_filter", "enrolled")
        inner = DemographicAnalyzer(adsl, population_filter=pop_filter)
        result = inner.analyze()

        pop_label = "Enrolled Analysis Set" if pop_filter == "enrolled" else "Safety Analysis Set"
        return self._result_to_tabledata(
            result,
            tlf_id="14.1.2.1",
            title="Demographic and Baseline Characteristics",
            population=pop_label,
            analysis_type="demographics",
            group_labels={1: "Arm 1", 2: "Arm 2", 3: "Arm 3"},
        )

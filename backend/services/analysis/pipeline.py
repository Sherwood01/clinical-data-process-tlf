"""Analyzer factory — maps analysis_type to analyzer class and dataset requirements.

Supports three categories of TLF outputs:
  - Tables: Statistical analysis tables (disposition, demographics, AE, etc.)
  - Figures: Clinical figures (KM plots, waterfall, swimmer, etc.)
  - Listings: Patient data listings (16.2.x.x)
"""
from typing import Dict, List, Optional

from backend.services.analysis.base_analyzer import BaseAnalyzer
from backend.services.analysis.models import AnalysisConfig, TableData
from backend.services.analysis.disposition_analyzer import DispositionAnalyzerWrapper
from backend.services.analysis.demographic_analyzer import DemographicAnalyzerWrapper
from backend.services.analysis.ae_summary_analyzer import AESummaryAnalyzerWrapper
from backend.services.analysis.survival_analyzer import SurvivalAnalyzerWrapper
from backend.services.analysis.laboratory_analyzer import LaboratoryAnalyzerWrapper
from backend.services.analysis.vital_signs_analyzer import VitalSignsAnalyzerWrapper

import pandas as pd

# Inline Wrappers for newly added TLF tables to keep files clean and cohesive
class MedicalHistoryAnalyzerWrapper(BaseAnalyzer):
    def analyze(self) -> TableData:
        from src.report.direct_generator import MedicalHistoryAnalyzer
        adsl = self._get_adsl()
        inner = MedicalHistoryAnalyzer(adsl)
        result = inner.analyze()
        return self._result_to_tabledata(
            result,
            tlf_id="14.1.3",
            title="Medical History Summary",
            population="Enrolled Analysis Set",
            analysis_type="medical_history",
        )

class MedicationAnalyzerWrapper(BaseAnalyzer):
    def analyze(self) -> TableData:
        from src.report.direct_generator import MedicationAnalyzer
        adcm = self.datasets.get("adcm", pd.DataFrame())
        adsl = self._get_adsl()
        inner = MedicationAnalyzer(adcm, adsl)
        result = inner.analyze()
        return self._result_to_tabledata(
            result,
            tlf_id="14.1.4",
            title="Medication Summary",
            population="Safety Analysis Set",
            analysis_type="medication",
        )

class ExposureAnalyzerWrapper(BaseAnalyzer):
    def analyze(self) -> TableData:
        from src.report.direct_generator import ExposureAnalyzer
        adex = self.datasets.get("adex", pd.DataFrame())
        adsl = self._get_adsl()
        inner = ExposureAnalyzer(adex, adsl)
        result = inner.analyze()
        return self._result_to_tabledata(
            result,
            tlf_id="14.1.5",
            title="Exposure Summary",
            population="Safety Analysis Set",
            analysis_type="exposure",
        )

class OverallSurvivalAnalyzerWrapper(BaseAnalyzer):
    def analyze(self) -> TableData:
        from src.report.direct_generator import OverallSurvivalAnalyzer
        adtte = self._get_adtte()
        adsl = self._get_adsl()
        inner = OverallSurvivalAnalyzer(adtte, adsl)
        result = inner.analyze()
        return self._result_to_tabledata(
            result,
            tlf_id="14.2.2.3",
            title="Overall Survival Summary",
            population="Full Analysis Set",
            analysis_type="overall_survival",
        )

# ── Table analyzers ──
ANALYSIS_TYPE_MAP: Dict[str, type] = {
    "disposition": DispositionAnalyzerWrapper,
    "demographics": DemographicAnalyzerWrapper,
    "ae_summary": AESummaryAnalyzerWrapper,
    "survival": SurvivalAnalyzerWrapper,
    "laboratory": LaboratoryAnalyzerWrapper,
    "vital_signs": VitalSignsAnalyzerWrapper,
    "medical_history": MedicalHistoryAnalyzerWrapper,
    "medication": MedicationAnalyzerWrapper,
    "exposure": ExposureAnalyzerWrapper,
    "overall_survival": OverallSurvivalAnalyzerWrapper,
}

# ── Figure types ──
FIGURE_TYPE_MAP: Dict[str, str] = {
    "km_os": "survival",
    "km_pfs": "survival",
    "waterfall": "response",
    "swimmer": "response",
    "spider": "response",
    "box_plot": "laboratory",
}

# ── Dataset requirements per analysis type ──
REQUIRED_DATASETS: Dict[str, List[str]] = {
    # Tables
    "disposition": ["adsl"],
    "demographics": ["adsl"],
    "ae_summary": ["adsl", "adae"],
    "survival": ["adsl", "adtte"],
    "laboratory": ["adsl", "adlb"],
    "vital_signs": ["adsl", "advs"],
    "medical_history": ["adsl"],
    "medication": ["adsl", "adcm"],
    "exposure": ["adsl", "adex"],
    "overall_survival": ["adsl", "adtte"],
    # Figures
    "km_os": ["adsl", "adtte"],
    "km_pfs": ["adsl", "adtte"],
    "waterfall": ["adsl", "adrs"],
    "swimmer": ["adsl", "adtte"],
    "spider": ["adsl", "adrs"],
    "box_plot": ["adsl", "adlb"],
    # Listings (commonly used datasets; others fallback to ["adsl"])
    "listing_16.2.1.1": ["adsl"],
    "listing_16.2.1.4": ["adsl", "adae"],
    "listing_16.2.2.1": ["adsl"],
    "listing_16.2.4.1": ["adsl", "adae"],
    "listing_16.2.5.1.1": ["adsl", "adlb"],
    "listing_16.2.6.1.1": ["adsl", "advs"],
}

# ── TLF ID prefix → analysis type (tables) ──
# Corrected 14.1.3 and 14.1.4, added 14.1.5 and specific overall survival mapping
TABLE_TLF_ID_PREFIX_MAP: Dict[str, str] = {
    "14.1.1": "disposition",
    "14.1.2": "demographics",
    "14.1.3": "medical_history",
    "14.1.4": "medication",
    "14.1.5": "exposure",
    "14.2.2.3": "overall_survival",
    "14.2": "survival",
    "14.3.1": "ae_summary",
    "14.4": "laboratory",
    "14.5": "vital_signs",
}

# ── TLF ID prefix → figure type ──
FIGURE_TLF_ID_PREFIX_MAP: Dict[str, str] = {
    "14.2.1": "km_os",
    "14.2.2": "km_pfs",
    "14.2.4.1": "waterfall",
    "14.2.4.3": "swimmer",
    "14.3.3": "box_plot",
}

# ── Listing IDs → listing type key ──
# Extracted from src/report/listing_generator.py to support full coverage
LISTING_ID_MAP: Dict[str, str] = {
    "16.2.1.1": "listing_16.2.1.1",
    "16.2.1.2": "listing_16.2.1.2",
    "16.2.1.3": "listing_16.2.1.3",
    "16.2.1.4": "listing_16.2.1.4",
    "16.2.2.1": "listing_16.2.2.1",
    "16.2.2.2": "listing_16.2.2.2",
    "16.2.2.3": "listing_16.2.2.3",
    "16.2.2.4": "listing_16.2.2.4",
    "16.2.4.1": "listing_16.2.4.1",
    "16.2.4.2": "listing_16.2.4.2",
    "16.2.4.3.1": "listing_16.2.4.3.1",
    "16.2.4.3.2": "listing_16.2.4.3.2",
    "16.2.4.5": "listing_16.2.4.5",
    "16.2.5.1.1": "listing_16.2.5.1.1",
    "16.2.5.1.2": "listing_16.2.5.1.2",
    "16.2.5.2.1": "listing_16.2.5.2.1",
    "16.2.5.2.3": "listing_16.2.5.2.3",
    "16.2.5.3.1": "listing_16.2.5.3.1",
    "16.2.5.3.3": "listing_16.2.5.3.3",
    "16.2.6.1.1": "listing_16.2.6.1.1",
}


def get_analyzer(analysis_type: str, datasets: Dict, config: AnalysisConfig = None) -> BaseAnalyzer:
    """Get a table analyzer instance for the given analysis type."""
    cls = ANALYSIS_TYPE_MAP.get(analysis_type)
    if not cls:
        raise ValueError(f"Unknown analysis type: '{analysis_type}'. Available: {list(ANALYSIS_TYPE_MAP.keys())}")
    return cls(datasets, config or AnalysisConfig())


def get_required_datasets(analysis_type: str) -> List[str]:
    """Get the list of required dataset names for an analysis/figure/listing type."""
    return REQUIRED_DATASETS.get(analysis_type, ["adsl"])


def infer_analysis_type(tlf_id: str, tlf_type: str = "table") -> str:
    """Infer the analysis type from a TLF ID and type.

    Performs startswith prefix matching sorted descending by string length
    to ensure most specific patterns match first (e.g. 14.2.2.3 matches before 14.2).
    """
    if tlf_type == "listing":
        sorted_listings = sorted(LISTING_ID_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        for lid, atype in sorted_listings:
            if tlf_id.startswith(lid):
                return atype
        return "generic"

    if tlf_type == "figure":
        sorted_figures = sorted(FIGURE_TLF_ID_PREFIX_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        for prefix, atype in sorted_figures:
            if tlf_id.startswith(prefix):
                return atype
        return "generic"

    # Default: table analysis
    sorted_tables = sorted(TABLE_TLF_ID_PREFIX_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    for prefix, atype in sorted_tables:
        if tlf_id.startswith(prefix):
            return atype
    return "generic"


def is_figure_type(analysis_type: str) -> bool:
    """Check if an analysis type is a figure type."""
    return analysis_type in FIGURE_TYPE_MAP


def is_listing_type(analysis_type: str) -> bool:
    """Check if an analysis type is a listing type."""
    return analysis_type in LISTING_ID_MAP.values()

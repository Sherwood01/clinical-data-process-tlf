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

# ── Table analyzers ──
ANALYSIS_TYPE_MAP: Dict[str, type] = {
    "disposition": DispositionAnalyzerWrapper,
    "demographics": DemographicAnalyzerWrapper,
    "ae_summary": AESummaryAnalyzerWrapper,
    "survival": SurvivalAnalyzerWrapper,
    "laboratory": LaboratoryAnalyzerWrapper,
    "vital_signs": VitalSignsAnalyzerWrapper,
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
    # Figures
    "km_os": ["adsl", "adtte"],
    "km_pfs": ["adsl", "adtte"],
    "waterfall": ["adsl", "adrs"],
    "swimmer": ["adsl", "adtte"],
    "spider": ["adsl", "adrs"],
    "box_plot": ["adsl", "adlb"],
    # Listings
    "listing_16.2.1.1": ["adsl"],
    "listing_16.2.1.4": ["adsl", "adae"],
}

# ── TLF ID prefix → analysis type (tables) ──
TABLE_TLF_ID_PREFIX_MAP: Dict[str, str] = {
    "14.1.1": "disposition",
    "14.1.2": "demographics",
    "14.1.3": "demographics",
    "14.1.4": "demographics",
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
LISTING_ID_MAP: Dict[str, str] = {
    "16.2.1.1": "listing_16.2.1.1",
    "16.2.1.4": "listing_16.2.1.4",
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

    Args:
        tlf_id: The TLF identifier, e.g. "14.1.1.1", "16.2.1.1"
        tlf_type: "table", "figure", or "listing"

    Returns:
        Analysis type string for the pipeline, or "generic"
    """
    if tlf_type == "listing":
        for lid, atype in LISTING_ID_MAP.items():
            if tlf_id.startswith(lid):
                return atype
        return "generic"

    if tlf_type == "figure":
        for prefix, atype in FIGURE_TLF_ID_PREFIX_MAP.items():
            if tlf_id.startswith(prefix):
                return atype
        return "generic"

    # Default: table analysis
    for prefix, atype in TABLE_TLF_ID_PREFIX_MAP.items():
        if tlf_id.startswith(prefix):
            return atype
    return "generic"


def is_figure_type(analysis_type: str) -> bool:
    """Check if an analysis type is a figure type."""
    return analysis_type in FIGURE_TYPE_MAP


def is_listing_type(analysis_type: str) -> bool:
    """Check if an analysis type is a listing type."""
    return analysis_type in LISTING_ID_MAP.values()

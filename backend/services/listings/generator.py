"""Listing generation service — wraps src/report/listing_generator.py for the SaaS pipeline.

Generates patient data listings (16.2.x) as PDF documents.

Key listings for MVP:
  - 16.2.1.1: Subject Disposition
  - 16.2.1.4: Death by Subject (SAE)
"""
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

logger = logging.getLogger("listing-generator")

# MVP listing IDs
SUPPORTED_LISTINGS = [
    "16.2.1.1",  # Subject Disposition
    "16.2.1.4",  # Death by Subject
]


@dataclass
class ListingConfig:
    """Configuration for listing generation."""
    listing_id: str
    population: str = "Enrolled Analysis Set"
    protocol: str = "xxxx-x-xxxx"
    company: str = "Daiichi Sankyo, Inc."


def generate_listing_pdf(
    datasets: Dict[str, pd.DataFrame],
    config: ListingConfig,
    output_pdf_path: str,
) -> str:
    """Generate a patient data listing PDF.

    Uses the existing src/report/listing_generator.py infrastructure:
    1. Builds listing data from raw DataFrames (bypasses file-based ListingAnalyzer)
    2. Generates PDF via PDFListingGenerator

    Args:
        datasets: Dict of ADaM dataset name → DataFrame
        config: Listing configuration
        output_pdf_path: Where to save the generated PDF

    Returns:
        Path to the generated PDF
    """
    from src.report.listing_generator import (
        LISTING_CONFIGS,
        COLUMN_DISPLAY_NAMES,
        PDFListingGenerator,
    )

    listing_config = LISTING_CONFIGS.get(config.listing_id)
    if not listing_config:
        raise ValueError(f"Unknown listing: {config.listing_id}")

    # Build listing data from in-memory DataFrames
    listing_data = _build_listing_data(datasets, listing_config, config)

    # Generate PDF
    os.makedirs(Path(output_pdf_path).parent, exist_ok=True)
    pdf_gen = PDFListingGenerator()
    pdf_gen.generate_pdf(
        listing_data=listing_data,
        output_path=output_pdf_path,
        protocol=config.protocol,
        company=config.company,
        analysis_set=config.population,
    )

    logger.info(
        f"Generated listing {config.listing_id}: "
        f"{listing_data['total_records']} records → {output_pdf_path}"
    )
    return output_pdf_path


def _build_listing_data(
    datasets: Dict[str, pd.DataFrame],
    listing_config: dict,
    config: ListingConfig,
) -> Dict[str, Any]:
    """Build listing data dict from in-memory DataFrames (bypasses file-based loader)."""
    from src.report.listing_generator import COLUMN_DISPLAY_NAMES

    required_datasets = listing_config["datasets"]
    primary_ds = required_datasets[0]
    df = datasets.get(primary_ds, pd.DataFrame()).copy()

    if df.empty:
        logger.warning(f"Primary dataset '{primary_ds}' empty for listing {config.listing_id}")
        return {
            "listing_id": config.listing_id,
            "name": listing_config.get("name", ""),
            "header": [],
            "columns": [],
            "data": [],
            "total_records": 0,
            "population": config.population,
        }

    # Normalize column names
    df.columns = [str(c) for c in df.columns]

    # Apply filters from config
    for filter_str in listing_config.get("filters", []):
        df = _apply_filter(df, filter_str)

    # Select available columns
    available_cols = set(df.columns)
    requested_cols = [c for c in listing_config["columns"] if c in available_cols]

    if not requested_cols:
        requested_cols = list(available_cols)[:15]  # Fallback

    # Sort by subject
    sort_cols = []
    for col in ["USUBJID", "SUBJID", "ADT", "VISIT"]:
        if col in df.columns:
            sort_cols.append(col)
    if sort_cols:
        try:
            df = df.sort_values(sort_cols)
        except Exception:
            pass

    # Build output rows
    header = [COLUMN_DISPLAY_NAMES.get(c, c) for c in requested_cols]
    data = []
    for _, row in df.iterrows():
        formatted_row = {}
        for c in requested_cols:
            val = row.get(c)
            formatted_row[COLUMN_DISPLAY_NAMES.get(c, c)] = _format_value(val)
        data.append(formatted_row)

    return {
        "listing_id": config.listing_id,
        "name": listing_config.get("name", ""),
        "header": header,
        "columns": requested_cols,
        "data": data,
        "total_records": len(data),
        "population": config.population,
    }


def _apply_filter(df: pd.DataFrame, filter_str: str) -> pd.DataFrame:
    """Apply a simple filter expression to a DataFrame."""
    if not filter_str:
        return df
    try:
        # Handle PARAMCD in (...)
        if "PARAMCD in" in filter_str or "PPCAT in" in filter_str or "TRGRESP in" in filter_str:
            import re
            # Extract values from parentheses
            match = re.search(r"in\s*\(([^)]+)\)", filter_str)
            if match:
                values = [v.strip().strip("'\"") for v in match.group(1).split(',')]
                col_match = re.match(r"(\w+)\s+in", filter_str)
                if col_match:
                    col = col_match.group(1)
                    if col in df.columns:
                        return df[df[col].isin(values)]
        elif "==" in filter_str:
            import re
            match = re.match(r"(\w+)=='([^']+)'", filter_str)
            if match:
                col, val = match.group(1), match.group(2)
                if col in df.columns:
                    return df[df[col] == val]
    except Exception:
        pass
    return df


def _format_value(val) -> str:
    """Format a value for display in listing."""
    if val is None:
        return ""
    if isinstance(val, float):
        import numpy as np
        if np.isnan(val):
            return ""
        if abs(val) >= 1000:
            return f"{val:.1f}"
        elif abs(val) >= 1:
            return f"{val:.2f}"
        else:
            return f"{val:.4f}"
    if isinstance(val, bytes):
        return val.decode()
    return str(val)


def get_required_datasets(listing_id: str) -> List[str]:
    """Return the list of ADaM datasets needed for a given listing."""
    from src.report.listing_generator import LISTING_CONFIGS
    config = LISTING_CONFIGS.get(listing_id, {})
    return config.get("datasets", ["adsl"])

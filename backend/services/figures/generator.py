"""Figure generation service — wraps src/report/figure_generator.py for the SaaS pipeline.

Generates KM survival plots as PNG images and wraps them into PDF pages
via reportlab for consistent output with table-based TLFs.
"""
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from backend.services.pdf.generator import PDFGenerator

logger = logging.getLogger("figure-generator")

FIGURE_TYPE_MAP = {
    "km_os": "survival",
    "km_pfs": "survival",
    "waterfall": "response",
    "swimmer": "response",
    "spider": "response",
    "box_plot": "laboratory",
}


@dataclass
class FigureConfig:
    """Configuration for figure generation."""
    tlf_id: str
    title: str
    population: str = ""
    figure_type: str = "km_os"
    width_inches: int = 8
    height_inches: int = 6
    dpi: int = 200


def generate_figure(
    datasets: Dict[str, pd.DataFrame],
    config: FigureConfig,
    output_path: str,
) -> str:
    """Generate a clinical figure and save to output_path.

    Supports KM plots, waterfall, swimmer, spider, and box plots.
    Delegates to the existing FigureGenerator from src/report/.
    """
    from src.report.figure_generator import (
        FigureGenerator,
        SurvivalFigureGenerator,
        ResponseFigureGenerator,
        LabFigureGenerator,
    )

    fig_type = config.figure_type
    os.makedirs(Path(output_path).parent, exist_ok=True)

    if fig_type == "km_os":
        adtte = datasets.get("adtte", pd.DataFrame())
        if adtte.empty:
            raise ValueError("ADTTE dataset required for KM OS figure")
        gen = SurvivalFigureGenerator()
        gen.generate_os_km(
            adttte=adtte,
            table_id=config.tlf_id,
            figure_title=config.title,
            population=config.population,
            output_path=output_path,
        )

    elif fig_type == "km_pfs":
        adtte = datasets.get("adtte", pd.DataFrame())
        if adtte.empty:
            raise ValueError("ADTTE dataset required for KM PFS figure")
        gen = SurvivalFigureGenerator()
        gen.generate_pfs_km(
            adttte=adtte,
            table_id=config.tlf_id,
            figure_title=config.title,
            population=config.population,
            output_path=output_path,
        )

    elif fig_type == "waterfall":
        adrs = datasets.get("adrs", pd.DataFrame())
        if adrs.empty:
            raise ValueError("ADRS dataset required for waterfall plot")
        gen = ResponseFigureGenerator()
        gen.generate_waterfall(
            adrs=adrs,
            table_id=config.tlf_id,
            output_path=output_path,
        )

    elif fig_type == "swimmer":
        adsl = datasets.get("adsl", pd.DataFrame())
        adtte = datasets.get("adtte")
        if adsl.empty:
            raise ValueError("ADSL dataset required for swimmer plot")
        gen = ResponseFigureGenerator()
        gen.generate_swimmer(
            adsl=adsl,
            adtte=adtte,
            table_id=config.tlf_id,
            output_path=output_path,
        )

    elif fig_type == "spider":
        adrs = datasets.get("adrs", pd.DataFrame())
        if adrs.empty:
            raise ValueError("ADRS dataset required for spider plot")
        gen = ResponseFigureGenerator()
        gen.generate_spider(
            adrs=adrs,
            table_id=config.tlf_id,
            output_path=output_path,
        )

    elif fig_type == "box_plot":
        adlb = datasets.get("adlb", pd.DataFrame())
        if adlb.empty:
            raise ValueError("ADLB dataset required for box plot")
        gen = LabFigureGenerator()
        gen.generate_lab_box(
            adlb=adlb,
            table_id=config.tlf_id,
            output_path=output_path,
        )

    else:
        raise ValueError(f"Unknown figure type: {fig_type}")

    logger.info(f"Generated figure: {output_path}")
    return output_path


def generate_figure_pdf(
    datasets: Dict[str, pd.DataFrame],
    config: FigureConfig,
    output_pdf_path: str,
) -> str:
    """Generate a figure, embed it into a PDF page, and return the PDF path.

    This produces a PDF that looks consistent with table-based TLF outputs,
    with the figure title/header rendered via reportlab.
    """
    # Generate the figure image first
    temp_dir = Path(output_pdf_path).parent
    os.makedirs(temp_dir, exist_ok=True)
    png_path = str(temp_dir / f"{config.tlf_id}_temp.png")

    try:
        generate_figure(datasets, config, png_path)

        # Wrap the PNG into a PDF via the PDF generator
        pdf_gen = PDFGenerator()
        pdf_gen.generate_figure(
            figure_path=png_path,
            title=config.title,
            population=config.population,
            tlf_id=config.tlf_id,
            output_path=output_pdf_path,
        )

        return output_pdf_path
    finally:
        # Clean up temp PNG
        if os.path.exists(png_path):
            os.unlink(png_path)


def get_required_datasets(figure_type: str) -> List[str]:
    """Return the list of ADaM datasets needed for a given figure type."""
    dataset_map = {
        "km_os": ["adsl", "adtte"],
        "km_pfs": ["adsl", "adtte"],
        "waterfall": ["adsl", "adrs"],
        "swimmer": ["adsl", "adtte"],
        "spider": ["adsl", "adrs"],
        "box_plot": ["adsl", "adlb"],
    }
    return dataset_map.get(figure_type, ["adsl"])

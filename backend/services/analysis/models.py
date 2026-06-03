"""Shared data models for the analysis pipeline."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Cell:
    """A single cell value in a table."""
    value: str


@dataclass
class Row:
    """A single row in a table."""
    label: str
    level: int  # 0=section header, 1=main, 2=sub
    cells: List[Cell]


@dataclass
class BigN:
    """Big N (sample size) by treatment group."""
    groups: Dict[int, int]       # treatment group number → N
    total: int                   # total N
    labels: Dict[int, str]       # treatment group number → display label


@dataclass
class AnalysisConfig:
    """Configuration for an analysis run."""
    population_filter: str = "enrolled"
    study_settings: Optional[dict] = None


@dataclass
class TableData:
    """Standard output from all analyzers."""
    tlf_id: str
    title: str
    population: str
    big_n: BigN
    headers: List[str]
    rows: List[Row]
    footnotes: List[str] = field(default_factory=list)
    analysis_type: str = "generic"

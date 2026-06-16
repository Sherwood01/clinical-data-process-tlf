"""Abstract base analyzer — wraps existing CLI analyzers from src/report/."""
from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd

from backend.services.analysis.models import AnalysisConfig, TableData


class BaseAnalyzer(ABC):
    """Abstract base for all TLF analyzers.

    Subclasses are thin wrappers around the existing analyzers in
    src/report/direct_generator.py. They delegate the actual statistical
    logic to the CLI code, converting results into the standard TableData format.
    """

    def __init__(self, datasets: Dict[str, pd.DataFrame], config: AnalysisConfig):
        self.datasets = datasets
        self.config = config

    @abstractmethod
    def analyze(self) -> TableData:
        """Run analysis and return structured TableData."""

    def _get_adsl(self) -> pd.DataFrame:
        """Get the ADSL dataset, or empty DataFrame if missing."""
        return self.datasets.get("adsl", pd.DataFrame())

    def _get_adae(self) -> pd.DataFrame:
        return self.datasets.get("adae", pd.DataFrame())

    def _get_adtte(self) -> pd.DataFrame:
        return self.datasets.get("adtte", pd.DataFrame())

    def _get_adlb(self) -> pd.DataFrame:
        return self.datasets.get("adlb", pd.DataFrame())

    def _get_advs(self) -> pd.DataFrame:
        return self.datasets.get("advs", pd.DataFrame())

    def _result_to_tabledata(
        self,
        result: dict,
        tlf_id: str,
        title: str,
        population: str,
        analysis_type: str = "generic",
        group_labels: Dict[int, str] = None,
    ) -> TableData:
        """Convert the common result dict format to TableData.

        All existing analyzers return {big_n, total_n, units} where
        each unit has {unit, level, rowlabel, col1, col2, col3, col_total}.
        """
        big_n_raw = result.get("big_n", {})
        group_labels = group_labels or {1: "Arm 1", 2: "Arm 2", 3: "Arm 3"}

        big_n = type("BigN", (), {})()
        big_n.groups = {int(k): int(v) for k, v in big_n_raw.items()}
        big_n.total = int(result.get("total_n", 0))
        big_n.labels = group_labels

        units = result.get("units", [])
        rows = []
        for u in units:
            col_keys = [k for k in sorted(u.keys()) if k.startswith("col") and k != "col_total"]
            cells = []
            for ck in col_keys:
                cells.append(self._make_cell(u.get(ck, "")))
            if "col_total" in u:
                cells.append(self._make_cell(u["col_total"]))
            rows.append(self._make_row(
                label=u.get("rowlabel", ""),
                level=int(u.get("level", 0)),
                cells=cells,
            ))

        headers = (group_labels.get(1, "Arm 1"), group_labels.get(2, "Arm 2"),
                   group_labels.get(3, "Arm 3"), "Total")

        from backend.services.analysis.models import BigN as BN, Row as R, Cell as C, TableData as TD
        return TD(
            tlf_id=tlf_id,
            title=title,
            population=population,
            big_n=BN(groups=big_n.groups, total=big_n.total, labels=big_n.labels),
            headers=list(headers),
            rows=rows,
            analysis_type=analysis_type,
        )

    def _make_cell(self, value) -> "Cell":
        from backend.services.analysis.models import Cell as C
        if isinstance(value, (int, float)):
            return C(value=str(value))
        return C(value=str(value or ""))

    def _make_row(self, label: str, level: int, cells: list) -> "Row":
        from backend.services.analysis.models import Row as R
        return R(label=label, level=level, cells=cells)

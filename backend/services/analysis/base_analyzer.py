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
        self.group_labels = {1: "Arm 1", 2: "Arm 2", 3: "Arm 3"}
        self._normalize_treatment_groups()

    @abstractmethod
    def analyze(self) -> TableData:
        """Run analysis and return structured TableData."""

    def _normalize_treatment_groups(self):
        """Analyze ADSL to map arbitrary treatment arm values dynamically to standard 1, 2, 3."""
        adsl = self._get_adsl()
        if adsl.empty:
            return

        # 1. Detect treatment column
        trt_col = None
        if "TRT01PN" in adsl.columns:
            trt_col = "TRT01PN"
        elif "TRT01P" in adsl.columns:
            trt_col = "TRT01P"
        elif "ARMCD" in adsl.columns:
            trt_col = "ARMCD"

        if not trt_col:
            return

        # Extract sorted unique non-null treatment values
        unique_trts = adsl[trt_col].dropna().unique()
        try:
            unique_trts = sorted(unique_trts)
        except Exception:
            unique_trts = list(unique_trts)

        if not unique_trts:
            return

        # 2. Build map: actual_value -> standard_index (1, 2, 3...)
        trt_map = {}
        for idx, trt_val in enumerate(unique_trts):
            std_val = idx + 1
            trt_map[trt_val] = std_val
            
            # Inject various casted keys to dodge Pandas type mapping mismatches
            try:
                val_float = float(trt_val)
                trt_map[val_float] = std_val
                if val_float.is_integer():
                    trt_map[int(val_float)] = std_val
            except (ValueError, TypeError):
                pass
                
            try:
                trt_map[str(trt_val)] = std_val
                if isinstance(trt_val, float) and trt_val.is_integer():
                    trt_map[str(int(trt_val))] = std_val
            except (ValueError, TypeError):
                pass

        # 3. Retrieve descriptive labels
        label_col = None
        for col in ["TRT01P", "ARM", "TRT01PN"]:
            if col in adsl.columns and col != trt_col:
                label_col = col
                break

        new_labels = {}
        for trt_val, std_val in trt_map.items():
            if trt_val not in unique_trts:
                continue
            label_name = None
            if label_col:
                subset = adsl[adsl[trt_col] == trt_val][label_col].dropna()
                if not subset.empty:
                    label_name = str(subset.iloc[0]).strip()
            if not label_name:
                label_name = f"Arm {trt_val}"
            new_labels[std_val] = label_name

        # Update labels and pad with empty strings for missing arms to preserve PDF column count
        if new_labels:
            for std_val in [1, 2, 3]:
                if std_val not in new_labels:
                    new_labels[std_val] = ""
            self.group_labels = new_labels

        # 4. Map values in all loaded datasets
        for name, df in list(self.datasets.items()):
            if df.empty:
                continue
            df_changed = False
            if "TRT01PN" in df.columns:
                df = df.copy()
                df["TRT01PN"] = df["TRT01PN"].map(trt_map).fillna(df["TRT01PN"])
                df_changed = True
            elif "TRT01P" in df.columns:
                df = df.copy()
                df["TRT01PN"] = df["TRT01P"].map(trt_map)
                df_changed = True

            if df_changed:
                self.datasets[name] = df

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
        
        # Override hardcoded default labels from child wrapper if we auto-derived real ones
        is_default = (
            group_labels is not None 
            and len(group_labels) == 3 
            and group_labels.get(1) == "Arm 1" 
            and group_labels.get(2) == "Arm 2" 
            and group_labels.get(3) == "Arm 3"
        )
        if group_labels is None or is_default:
            group_labels = self.group_labels

        big_n = type("BigN", (), {})()
        big_n.groups = {int(k): int(v) for k, v in big_n_raw.items()}
        
        # Fallback to sum of groups if total_n is zero or omitted
        total_n = int(result.get("total_n", 0))
        if total_n == 0 and big_n.groups:
            total_n = sum(big_n.groups.values())
        big_n.total = total_n
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

        headers = (group_labels.get(1, "Arm 1") or "", group_labels.get(2, "Arm 2") or "",
                   group_labels.get(3, "Arm 3") or "", "Total")

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

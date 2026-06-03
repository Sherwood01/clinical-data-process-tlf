"""
Generic TLF Analyzer - Template-driven statistical analysis.

Uses ICH E3 templates to define analysis structure, then executes
generic statistical analysis on ADaM datasets.
"""

import pyreadstat
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class VariableSpec:
    """Specification for a variable to analyze."""
    var_name: str           # ADaM variable name (e.g., "AGE", "SEX")
    row_label: str          # Display label for the row
    stat_type: str          # "categorical", "continuous", "flag"
    level: int = 1         # Hierarchy level for indentation
    parent_label: str = ""  # Parent row label for grouping
    # For categorical: list of values to display
    values: List[Tuple[str, str]] = None  # [(value, label), ...]
    # For categorical: whether to show n (%)
    show_n_pct: bool = True


@dataclass
class AnalysisTemplate:
    """
    Template for a TLF analysis.

    Defines what variables to analyze, how to stratify, and what rows to produce.
    """
    tlf_id: str
    tlf_name: str
    population: str                    # Population flag: "ENRLFL", "SAFFL", etc.
    population_value: str = "Y"        # Value of population flag to filter on
    strata: str = "TRT01PN"           # Stratification variable (treatment group)
    strata_labels: Dict[int, str] = None  # {1: "5.4 mg/kg", 2: "6.4 mg/kg", 3: "7.4 mg/kg"}
    variables: List[VariableSpec] = field(default_factory=list)
    big_n_unit: str = "big_n"          # Unit name for Big N row


# Default strata labels
DEFAULT_STRATA_LABELS = {
    1: "5.4 mg/kg",
    2: "6.4 mg/kg",
    3: "7.4 mg/kg"
}

# Standard population flags
POPULATION_FLAGS = {
    "Enrolled Analysis Set": ("ENRLFL", "Y"),
    "Safety Analysis Set": ("SAFFL", "Y"),
    "Response Evaluable Set": ("RESFL", "Y"),
    "PK Analysis Set": ("PKFL", "Y"),
}


# ============================================================================
# Analysis Templates for Section 14.1.x
# ============================================================================

TEMPLATES_14_1_1 = {
    "14.1.1.1": AnalysisTemplate(
        tlf_id="14.1.1.1",
        tlf_name="Subject Disposition",
        population="ENRLFL",
        variables=[
            VariableSpec("SCRNFL", "No. of Subjects Screened", "flag", level=1),
            VariableSpec("SCNEFL", "No. of Subjects Screen Failed", "flag", level=1),
            VariableSpec("ENRLFL", "Enrolled Analysis Set (EAS)", "flag", level=2),
            VariableSpec("SAFFL", "Safety Analysis Set", "flag", level=2),
            VariableSpec("RESFL", "Response Evaluable Set", "flag", level=2),
            VariableSpec("PKFL", "PK Analysis Set", "flag", level=2),
            VariableSpec("ONGFL", "Ongoing", "flag", level=2),
            VariableSpec("DISCTFL", "Discontinued", "flag", level=2),
        ]
    ),
}

TEMPLATES_14_1_2 = {
    "14.1.2.1": AnalysisTemplate(
        tlf_id="14.1.2.1",
        tlf_name="Demographic and Baseline Characteristics",
        population="ENRLFL",
        variables=[
            VariableSpec("AGE", "Age (years)", "continuous", level=1),
            VariableSpec("AGEGR", "Age Group", "categorical", level=1,
                        values=[("<65", "<65"), (">=65", ">=65")]),
            VariableSpec("SEX", "Sex", "categorical", level=1,
                        values=[("F", "Female"), ("M", "Male")]),
            VariableSpec("RACE", "Race", "categorical", level=1),
            VariableSpec("ETHNIC", "Ethnicity", "categorical", level=1),
            VariableSpec("REGION1", "Region", "categorical", level=1),
            VariableSpec("ECOGBL", "ECOG Performance Status at Baseline", "categorical", level=1),
        ]
    ),
    "14.1.2.2": AnalysisTemplate(
        tlf_id="14.1.2.2",
        tlf_name="Demographic and Baseline Characteristics by Region/Country",
        population="ENRLFL",
        variables=[
            VariableSpec("AGE", "Age (years)", "continuous", level=1),
            VariableSpec("AGEGR", "Age Group", "categorical", level=1,
                        values=[("<65", "<65"), (">=65", ">=65")]),
            VariableSpec("SEX", "Sex", "categorical", level=1,
                        values=[("F", "Female"), ("M", "Male")]),
            VariableSpec("RACE", "Race", "categorical", level=1),
            VariableSpec("ETHNIC", "Ethnicity", "categorical", level=1),
            VariableSpec("REGION1", "Region", "categorical", level=1),
            VariableSpec("ECOGBL", "ECOG Performance Status at Baseline", "categorical", level=1),
            VariableSpec("COUNTRY", "Country", "categorical", level=1),
        ]
    ),
    "14.1.2.3": AnalysisTemplate(
        tlf_id="14.1.2.3",
        tlf_name="Demographic and Baseline Characteristics (Safety Analysis Set)",
        population="SAFFL",
        variables=[
            VariableSpec("AGE", "Age (years)", "continuous", level=1),
            VariableSpec("AGEGR", "Age Group", "categorical", level=1,
                        values=[("<65", "<65"), (">=65", ">=65")]),
            VariableSpec("SEX", "Sex", "categorical", level=1,
                        values=[("F", "Female"), ("M", "Male")]),
            VariableSpec("RACE", "Race", "categorical", level=1),
            VariableSpec("ETHNIC", "Ethnicity", "categorical", level=1),
            VariableSpec("REGION1", "Region", "categorical", level=1),
            VariableSpec("ECOGBL", "ECOG Performance Status at Baseline", "categorical", level=1),
        ]
    ),
    "14.1.2.4": AnalysisTemplate(
        tlf_id="14.1.2.4",
        tlf_name="Demographic and Baseline Characteristics by Region/Country (Safety)",
        population="SAFFL",
        variables=[
            VariableSpec("AGE", "Age (years)", "continuous", level=1),
            VariableSpec("AGEGR", "Age Group", "categorical", level=1,
                        values=[("<65", "<65"), (">=65", ">=65")]),
            VariableSpec("SEX", "Sex", "categorical", level=1,
                        values=[("F", "Female"), ("M", "Male")]),
            VariableSpec("RACE", "Race", "categorical", level=1),
            VariableSpec("ETHNIC", "Ethnicity", "categorical", level=1),
            VariableSpec("REGION1", "Region", "categorical", level=1),
            VariableSpec("ECOGBL", "ECOG Performance Status at Baseline", "categorical", level=1),
            VariableSpec("COUNTRY", "Country", "categorical", level=1),
        ]
    ),
}

# ============================================================================
# Analysis Templates for Section 14.1.3 (Medical History)
# ============================================================================

TEMPLATES_14_1_3 = {
    "14.1.3.1": AnalysisTemplate(
        tlf_id="14.1.3.1",
        tlf_name="Medical History and Disease Characteristics",
        population="ENRLFL",
        variables=[
            VariableSpec("DURDIAG", "Time from Initial Histological Diagnosis to Study Treatment (Months)", "continuous", level=1),
            VariableSpec("HIST", "Histology", "categorical", level=1),
            VariableSpec("STAGESE", "Tumor Stage at Study Entry", "categorical", level=1),
        ]
    ),
}

# ============================================================================
# Analysis Templates for Section 14.1.4 (Prior/Concomitant Medications)
# ============================================================================

TEMPLATES_14_1_4 = {
    "14.1.4.1": AnalysisTemplate(
        tlf_id="14.1.4.1",
        tlf_name="Prior Medication",
        population="ENRLFL",
        variables=[
            VariableSpec("CMCLAS", "Medication Class", "categorical", level=1),
            VariableSpec("CMTRT", "Medication", "categorical", level=1),
        ]
    ),
    "14.1.4.2": AnalysisTemplate(
        tlf_id="14.1.4.2",
        tlf_name="Concomitant Medication",
        population="ENRLFL",
        variables=[
            VariableSpec("CMCLAS", "Medication Class", "categorical", level=1),
            VariableSpec("CMTRT", "Medication", "categorical", level=1),
        ]
    ),
}

# ============================================================================
# Analysis Templates for Section 14.1.5 (Exposure)
# ============================================================================

TEMPLATES_14_1_5 = {
    "14.1.5.1": AnalysisTemplate(
        tlf_id="14.1.5.1",
        tlf_name="Study Drug Exposure",
        population="SAFFL",
        variables=[
            VariableSpec("EXDOSE", "Dose (mg/kg)", "continuous", level=1),
            VariableSpec("EXDY", "Duration of Treatment (Days)", "continuous", level=1),
            VariableSpec("EXTOT", "Total Cumulative Dose (mg/kg)", "continuous", level=1),
        ]
    ),
}

# ============================================================================
# Analysis Templates for Section 14.2 (Efficacy)
# ============================================================================

TEMPLATES_14_2 = {
    "14.2.1.1": AnalysisTemplate(
        tlf_id="14.2.1.1",
        tlf_name="Best Overall Response",
        population="RESFL",
        variables=[
            VariableSpec("BESTRESP", "Best Overall Response", "categorical", level=1,
                        values=[("CR", "Complete Response (CR)"), ("PR", "Partial Response (PR)"),
                                ("SD", "Stable Disease (SD)"), ("PD", "Progressive Disease (PD)"),
                                ("NE", "Not Evaluable (NE)")]),
        ]
    ),
    "14.2.1.2": AnalysisTemplate(
        tlf_id="14.2.1.2",
        tlf_name="Objective Response Rate",
        population="RESFL",
        variables=[
            VariableSpec("RESPFL", "Objective Response (CR+PR)", "flag", level=1),
        ]
    ),
    "14.2.3.1": AnalysisTemplate(
        tlf_id="14.2.3.1",
        tlf_name="Best Change in Sum of Target Lesions",
        population="RESFL",
        variables=[
            VariableSpec("BESTRESP", "Best Overall Response", "categorical", level=1,
                        values=[("CR/PR", "Good (CR/PR)"), ("SD", "Intermediate (SD)"),
                                ("PD", "Poor (PD)")]),
        ]
    ),
    "14.2.4.1": AnalysisTemplate(
        tlf_id="14.2.4.1",
        tlf_name="Waterfall Plot - Best Overall Response",
        population="RESFL",
        variables=[
            VariableSpec("BESTRESP", "Best Overall Response", "categorical", level=1),
        ]
    ),
    "14.2.5.1": AnalysisTemplate(
        tlf_id="14.2.5.1",
        tlf_name="Subgroup Analysis - Best Overall Response",
        population="RESFL",
        variables=[
            VariableSpec("AGEGR", "Age Group", "categorical", level=1),
            VariableSpec("SEX", "Sex", "categorical", level=1),
        ]
    ),
}

# ============================================================================
# Analysis Templates for Section 14.3 (Safety)
# ============================================================================

TEMPLATES_14_3 = {
    "14.3.1.1": AnalysisTemplate(
        tlf_id="14.3.1.1",
        tlf_name="Overall Summary of Treatment-Emergent Adverse Events",
        population="SAFFL",
        variables=[
            VariableSpec("TRTEMFL", "Subjects with any TEAE", "flag", level=1),
            VariableSpec("AETOXGR", "Grade 3 or Higher TEAE", "flag", level=1),
        ]
    ),
    "14.3.2.1": AnalysisTemplate(
        tlf_id="14.3.2.1",
        tlf_name="Deaths",
        population="SAFFL",
        variables=[
            VariableSpec("DTHFL", "Deaths", "flag", level=1),
        ]
    ),
    "14.3.5.1": AnalysisTemplate(
        tlf_id="14.3.5.1",
        tlf_name="ECG Findings",
        population="SAFFL",
        variables=[
            VariableSpec("ECGORES", "ECG Result", "categorical", level=1,
                        values=[("NORMAL", "Normal"), ("ABNORMAL", "Abnormal")]),
        ]
    ),
    "14.3.5.2": AnalysisTemplate(
        tlf_id="14.3.5.2",
        tlf_name="Biochemistry Findings",
        population="SAFFL",
        variables=[
            VariableSpec("LBORES", "Biochemistry Result", "categorical", level=1,
                        values=[("NORMAL", "Normal"), ("ABNORMAL", "Abnormal")]),
        ]
    ),
}

# ============================================================================
# Analysis Templates for Section 14.4 (PK)
# ============================================================================

TEMPLATES_14_4 = {
    "14.4.1.1": AnalysisTemplate(
        tlf_id="14.4.1.1",
        tlf_name="Plasma PK Parameters",
        population="PKFL",
        variables=[
            VariableSpec("CMAX", "Cmax (ng/mL)", "continuous", level=1),
            VariableSpec("AUC0T", "AUC0-t (ng.h/mL)", "continuous", level=1),
            VariableSpec("AUC0INF", "AUC0-inf (ng.h/mL)", "continuous", level=1),
            VariableSpec("TMAX", "Tmax (h)", "continuous", level=1),
            VariableSpec("TLAG", "Tlag (h)", "continuous", level=1),
            VariableSpec("THALF", "t1/2 (h)", "continuous", level=1),
            VariableSpec("CLF", "CL/F (mL/h)", "continuous", level=1),
            VariableSpec("VZF", "Vz/F (mL)", "continuous", level=1),
        ]
    ),
    "14.4.2.1": AnalysisTemplate(
        tlf_id="14.4.2.1",
        tlf_name="Urine PK Parameters",
        population="PKFL",
        variables=[
            VariableSpec("AETOT", "Ae (mg)", "continuous", level=1),
            VariableSpec("FETOT", "Fe (%)", "continuous", level=1),
            VariableSpec("CLR", "CLR (mL/h)", "continuous", level=1),
        ]
    ),
}


# Registry of all templates
ALL_TEMPLATES = {}
ALL_TEMPLATES.update(TEMPLATES_14_1_1)
ALL_TEMPLATES.update(TEMPLATES_14_1_2)
ALL_TEMPLATES.update(TEMPLATES_14_1_3)
ALL_TEMPLATES.update(TEMPLATES_14_1_4)
ALL_TEMPLATES.update(TEMPLATES_14_1_5)
ALL_TEMPLATES.update(TEMPLATES_14_2)
ALL_TEMPLATES.update(TEMPLATES_14_3)
ALL_TEMPLATES.update(TEMPLATES_14_4)


def get_template(tlf_id: str) -> Optional[AnalysisTemplate]:
    """Get analysis template for a given TLF ID."""
    # Try exact match first
    if tlf_id in ALL_TEMPLATES:
        return ALL_TEMPLATES[tlf_id]

    # Try without "Table " prefix
    clean_id = tlf_id.replace("Table ", "")
    if clean_id in ALL_TEMPLATES:
        return ALL_TEMPLATES[clean_id]

    return None


class GenericAnalyzer:
    """
    Generic analyzer that executes analysis based on template.
    """

    def __init__(self, adsl: pd.DataFrame, template: AnalysisTemplate):
        self.adsl = adsl
        self.template = template
        self.strata_labels = template.strata_labels or DEFAULT_STRATA_LABELS

    def _filter_population(self) -> pd.DataFrame:
        """Filter to analysis population."""
        pop_var = self.template.population
        pop_val = self.template.population_value
        if pop_var in self.adsl.columns:
            return self.adsl[self.adsl[pop_var] == pop_val].copy()
        return self.adsl.copy()

    def _calculate_big_n(self, df: pd.DataFrame) -> Dict[int, int]:
        """Calculate Big N by treatment group."""
        big_n = {}
        for trt in self.strata_labels.keys():
            big_n[trt] = len(df[df[self.template.strata] == trt])
        return big_n

    def _format_n_pct(self, count: int, denom: int) -> str:
        """Format count and percentage."""
        if denom == 0:
            return "0 (0.0%)"
        pct = count / denom * 100
        return f"{count} ({pct:.1f}%)"

    def _format_continuous_stats(self, series: pd.Series) -> Dict[str, float]:
        """Calculate continuous statistics."""
        valid = series.dropna()
        if len(valid) == 0:
            return {'n': 0, 'mean': np.nan, 'std': np.nan, 'median': np.nan, 'min': np.nan, 'max': np.nan}
        return {
            'n': len(valid),
            'mean': valid.mean(),
            'std': valid.std(),
            'median': valid.median(),
            'min': valid.min(),
            'max': valid.max()
        }

    def analyze(self) -> Dict[str, Any]:
        """
        Perform analysis based on template.

        Returns:
            Dict with:
            - big_n: {treatment: count}
            - total_n: total subjects
            - units: list of row data
        """
        template = self.template
        df = self._filter_population()

        big_n = self._calculate_big_n(df)
        total_n = sum(big_n.values())

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        # Add Big N row
        results['units'].append({
            'unit': 'big_n',
            'level': 0,
            'rowlabel': 'Subjects in Population',
            'col1': str(big_n.get(1, 0)),
            'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)),
            'col_total': str(total_n)
        })

        # Analyze each variable
        for var_spec in template.variables:
            if var_spec.stat_type == "continuous":
                self._analyze_continuous(df, big_n, var_spec, results)
            elif var_spec.stat_type == "categorical":
                self._analyze_categorical(df, big_n, var_spec, results)
            elif var_spec.stat_type == "flag":
                self._analyze_flag(df, big_n, var_spec, results)

        return results

    def _analyze_continuous(self, df: pd.DataFrame, big_n: Dict[int, int],
                           var_spec: VariableSpec, results: Dict):
        """Analyze a continuous variable."""
        # Header row
        results['units'].append({
            'unit': var_spec.var_name,
            'level': var_spec.level,
            'rowlabel': var_spec.row_label,
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Collect stats for all treatment groups
        all_stats = {}
        for trt in [1, 2, 3]:
            subset = df[df[self.template.strata] == trt][var_spec.var_name]
            all_stats[trt] = self._format_continuous_stats(subset)

        # Mean (SD) row
        mean_row = {'unit': var_spec.var_name, 'level': var_spec.level + 1,
                    'rowlabel': '  Mean (SD)', 'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        for trt in [1, 2, 3]:
            stats = all_stats[trt]
            if stats['n'] > 0:
                mean_row[f'col{trt}'] = f"{stats['mean']:.1f} ({stats['std']:.1f})"
        results['units'].append(mean_row)

        # Median (Min, Max) row
        median_row = {'unit': var_spec.var_name, 'level': var_spec.level + 1,
                      'rowlabel': '  Median (Min, Max)', 'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        for trt in [1, 2, 3]:
            stats = all_stats[trt]
            if stats['n'] > 0:
                median_row[f'col{trt}'] = f"{stats['median']:.1f} ({stats['min']:.0f}, {stats['max']:.0f})"
        results['units'].append(median_row)

    def _analyze_categorical(self, df: pd.DataFrame, big_n: Dict[int, int],
                             var_spec: VariableSpec, results: Dict):
        """Analyze a categorical variable."""
        # Header row
        results['units'].append({
            'unit': var_spec.var_name,
            'level': var_spec.level,
            'rowlabel': var_spec.row_label,
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Get unique values if not specified
        if var_spec.values:
            values_to_analyze = var_spec.values
        else:
            values_to_analyze = [(v, v) for v in df[var_spec.var_name].dropna().unique()]

        for value, label in values_to_analyze:
            row = {'unit': var_spec.var_name, 'level': var_spec.level + 1,
                   'rowlabel': f'  {label}', 'col1': '', 'col2': '', 'col3': '', 'col_total': ''}

            total_count = 0
            for trt in [1, 2, 3]:
                subset = df[df[self.template.strata] == trt]
                count = len(subset[subset[var_spec.var_name] == value])
                denom = big_n.get(trt, 0)
                row[f'col{trt}'] = self._format_n_pct(count, denom)
                total_count += count

            row['col_total'] = self._format_n_pct(total_count, results['total_n'])
            results['units'].append(row)

    def _analyze_flag(self, df: pd.DataFrame, big_n: Dict[int, int],
                     var_spec: VariableSpec, results: Dict):
        """Analyze a flag variable (Y/N)."""
        results['units'].append({
            'unit': var_spec.var_name,
            'level': var_spec.level,
            'rowlabel': var_spec.row_label,
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })


def generic_analyze(adsl: pd.DataFrame, tlf_id: str) -> Dict[str, Any]:
    """
    Generic analysis function for any TLF.

    Args:
        adsl: ADSL DataFrame
        tlf_id: TLF ID (e.g., "14.1.2.1" or "Table 14.1.2.1")

    Returns:
        Analysis results dict with big_n, total_n, and units
    """
    template = get_template(tlf_id)
    if template is None:
        raise ValueError(f"No template found for {tlf_id}")

    analyzer = GenericAnalyzer(adsl, template)
    return analyzer.analyze()


if __name__ == "__main__":
    # Test
    base = Path("d:/hello world/clinical-data-process")
    adsl_path = base / "input/ADaM/Data/adsl.sas7bdat"

    adsl, _ = pyreadstat.read_sas7bdat(str(adsl_path))
    print(f"Loaded ADSL: {len(adsl)} rows")

    # Test template 14.1.2.1
    template = get_template("14.1.2.1")
    print(f"\nTemplate: {template.tlf_id}")
    print(f"Name: {template.tlf_name}")
    print(f"Population: {template.population}")
    print(f"Variables: {[v.var_name for v in template.variables]}")

    # Run analysis
    results = generic_analyze(adsl, "14.1.2.1")
    print(f"\nBig N: {results['big_n']}")
    print(f"Total N: {results['total_n']}")
    print(f"Units: {len(results['units'])}")
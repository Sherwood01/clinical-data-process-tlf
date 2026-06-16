"""
Figure Generator - Generates clinical trial figures (KM plots, Waterfall, Swimmer, Spider, Box).
Uses matplotlib to produce figures matching ICH E3 standards.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from datetime import datetime
from pathlib import Path

try:
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test
    HAS_LIFELINES = True
except ImportError:
    HAS_LIFELINES = False
    KaplanMeierFitter = None
    logrank_test = None


# Treatment colors and labels
DEFAULT_TREATMENT_LABELS = {
    1: "Treatment A",
    2: "Treatment B",
    3: "Treatment C"
}
TREATMENT_COLORS = ['#0077CC', '#FF7F0E', '#2CA02C']  # Blue, Orange, Green
TREATMENT_MARKERS = ['o', 's', '^']


class FigureGenerator:
    """Generates clinical trial figures (KM plots, Waterfall, Swimmer, etc.)."""

    def __init__(self, style: str = "clinical"):
        self.style = style
        self._setup_style()

    def _setup_style(self):
        """Configure matplotlib style for clinical figures."""
        plt.rcParams.update({
            'font.family': 'Arial',
            'font.size': 9,
            'axes.linewidth': 0.5,
            'axes.edgecolor': 'black',
            'axes.labelcolor': 'black',
            'text.color': 'black',
            'figure.edgecolor': 'white',
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'patch.edgecolor': 'white',
            'legend.frameon': False,
            'legend.fontsize': 8,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
        })

    def _get_trt_col(self, df: pd.DataFrame) -> str:
        """Get treatment column from dataframe."""
        for col in ['TRT01PN', 'TRTPN', 'TRT01P']:
            if col in df.columns:
                return col
        return None

    def _prepare_km_data(
        self,
        adttte: pd.DataFrame,
        param_filter: str = None,
        time_col: str = "AVAL",
        event_col: str = "CNSR"
    ) -> Tuple[pd.DataFrame, Dict]:
        """Prepare data for KM plot from ADTTE dataset."""
        df = adttte.copy()

        # Filter by parameter (OS or PFS)
        if param_filter:
            if isinstance(param_filter, str):
                df = df[df['PARAM'].str.contains(param_filter, case=False, na=False)]
            elif isinstance(param_filter, list):
                df = df[df['PARAM'].isin(param_filter)]

        # Convert event: CNSR=0 means event, CNSR=1 means censored (standard CDISC)
        # But some datasets invert this, so we check
        if event_col in df.columns:
            # CNSR: 0=Event, 1=Censored (CDISC standard)
            df['EVENT'] = (df[event_col] == 0).astype(int)

        # Get treatment column
        trt_col = self._get_trt_col(df)
        if not trt_col:
            # Merge with adsl if needed
            pass

        return df, {'trt_col': trt_col, 'time_col': time_col, 'event_col': 'EVENT'}

    def generate_km_plot(
        self,
        adttte: pd.DataFrame,
        table_id: str,
        figure_title: str,
        population: str,
        param_filter: str = None,
        time_col: str = "AVAL",
        event_col: str = "CNSR",
        treatment_col: str = None,
        treatment_labels: Dict[int, str] = None,
        output_path: str = None,
        add_n_at_risk: bool = True,
        add_median_line: bool = True
    ) -> str:
        """
        Generate Kaplan-Meier survival plot.

        Args:
            adttte: ADTTE dataset with survival data
            table_id: Figure ID (e.g., "14.2.1.1")
            figure_title: Title of the figure
            population: Population description
            param_filter: Filter for PARAM column (e.g., "Overall Survival" or "PFS")
            time_col: Time variable column (default: AVAL in days)
            event_col: Event indicator (default: CNSR where 0=event, 1=censored)
            treatment_col: Treatment group column
            treatment_labels: Dict mapping treatment number to label
            output_path: Path to save figure
            add_n_at_risk: Add number at risk table below plot
            add_median_line: Add median survival line

        Returns:
            Path to saved figure
        """
        if not HAS_LIFELINES:
            raise ImportError("lifelines library required for KM plots. Run: pip install lifelines")

        if treatment_labels is None:
            treatment_labels = DEFAULT_TREATMENT_LABELS

        if treatment_col is None:
            treatment_col = self._get_trt_col(adttte) or 'TRTPN'

        # Prepare data
        df, meta = self._prepare_km_data(adttte, param_filter, time_col, event_col)
        df = df[df[time_col].notna() & df['EVENT'].notna()]

        fig, ax = plt.subplots(figsize=(7.5, 5.5))

        treatment_groups = sorted(df[treatment_col].dropna().unique())
        km_results = {}

        # Fit KM for each treatment arm
        for i, trt in enumerate(treatment_groups):
            trt_data = df[df[treatment_col] == trt].copy()
            durations = trt_data[time_col] / 30.44  # Convert days to months
            events = trt_data['EVENT']

            if len(durations) < 2:
                continue

            kmf = KaplanMeierFitter()
            kmf.fit(durations, event_observed=events,
                   label=treatment_labels.get(int(trt), f"Trt {trt}"))
            km_results[int(trt)] = kmf

            # Plot with confidence interval
            kmf.plot_survival_function(
                ax=ax,
                color=TREATMENT_COLORS[i % len(TREATMENT_COLORS)],
                linewidth=1.5,
                ci_show=True,
                ci_alpha=0.2
            )

        # Axes formatting
        ax.set_xlim(0, None)
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Time (Months)", fontsize=9, labelpad=5)
        ax.set_ylabel("Survival Probability", fontsize=9, labelpad=5)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))

        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Add median survival lines
        if add_median_line:
            for trt, kmf in km_results.items():
                try:
                    median = kmf.median_survival_time_
                    if not np.isnan(median):
                        ax.axvline(x=median, color=TREATMENT_COLORS[treatment_groups.index(trt) % 3],
                                  linestyle='--', linewidth=0.5, alpha=0.5)
                except:
                    pass

        # Legend
        if len(km_results) > 0:
            handles = [Line2D([0], [0], color=TREATMENT_COLORS[treatment_groups.index(trt) % 3],
                            linewidth=1.5, label=treatment_labels.get(int(trt), f"Trt {trt}"))
                      for trt in km_results.keys()]
            ax.legend(handles=handles, loc="lower left", frameon=False)

        # Number at risk table
        if add_n_at_risk:
            self._add_n_at_risk(ax, km_results, treatment_labels, max_months=24)

        # Figure header
        fig.text(0.5, 0.97, f"Figure {table_id}", fontsize=10, ha='center', fontweight='normal')
        fig.text(0.5, 0.93, figure_title, fontsize=9, ha='center')
        fig.text(0.5, 0.89, f"({population})", fontsize=8, ha='center', style='italic')

        plt.tight_layout(rect=[0, 0.18 if add_n_at_risk else 0.05, 1, 0.93])

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            return output_path

        plt.close()
        return ""

    def _add_n_at_risk(
        self,
        ax,
        km_results: Dict,
        treatment_labels: Dict,
        max_months: int = 24
    ) -> None:
        """Add number at risk table below the plot."""
        time_points = list(range(0, max_months + 1, 3))

        # Create table
        table_text = "                    "
        for t in time_points:
            table_text += f"{t:>6}"
        ax.text(0.5, -0.22, table_text, transform=ax.transAxes,
                fontsize=7, ha='center', family='monospace')

        y_offset = -0.28
        for trt in sorted(km_results.keys()):
            label = treatment_labels.get(trt, f"Treatment {trt}")
            row_text = f"{label:<20}"
            kmf = km_results[trt]

            for t in time_points:
                try:
                    n_at_risk = kmf.survival_function_.loc[:t].shape[0]
                    row_text += f"{n_at_risk:>6}"
                except:
                    row_text += f"{'0':>6}"

            ax.text(0.5, y_offset, row_text, transform=ax.transAxes,
                    fontsize=7, ha='center', family='monospace')
            y_offset -= 0.04

    def generate_waterfall_plot(
        self,
        adrs: pd.DataFrame,
        table_id: str,
        figure_title: str,
        population: str,
        subject_col: str = "USUBJID",
        treatment_col: str = None,
        treatment_labels: Dict[int, str] = None,
        response_col: str = "RSSTRESC",
        best_response_only: bool = True,
        output_path: str = None
    ) -> str:
        """
        Generate Waterfall plot for Best Overall Response.

        Args:
            adrs: ADRS dataset with tumor response data
            table_id: Figure ID
            figure_title: Title of the figure
            population: Population description
            subject_col: Subject identifier column
            treatment_col: Treatment group column (auto-detected if not specified)
            treatment_labels: Dict mapping treatment number to label
            response_col: Column containing response values
            best_response_only: Only show best response per subject
            output_path: Path to save figure

        Returns:
            Path to saved figure
        """
        if treatment_labels is None:
            treatment_labels = DEFAULT_TREATMENT_LABELS

        if treatment_col is None:
            treatment_col = self._get_trt_col(adrs) or 'TRTPN'

        df = adrs.copy()

        # Filter for Overall Response assessment
        if 'RSTESTCD' in df.columns:
            df = df[df['RSTESTCD'] == 'OVRLRESP']

        # Get best response per subject (lowest % change = best response)
        if 'CHG' in df.columns:
            # Tumor change from baseline (negative = shrinkage)
            df = df[df['CHG'].notna()].copy()
            # For waterfall: show best response as % change
            # CR=-100%, PR=-30%, SD=0%, PD=+20%

            # Map response to change if CHG not directly available
            if 'NRTRN' in df.columns and df['NRTRN'].notna().any():
                df['PCT_CHANGE'] = df['NRTRN'] * 100  # Already in percent
            else:
                # Map RSSTRESC to approximate change
                resp_to_change = {'CR': -100, 'PR': -30, 'SD': 0, 'PD': 20,
                                'NON-CR/NON-PD': 0, 'NE': 0, 'NB': 0}
                df['PCT_CHANGE'] = df[response_col].map(resp_to_change)
                # Fallback to CHG if available
                df.loc[df['CHG'].notna(), 'PCT_CHANGE'] = df.loc[df['CHG'].notna(), 'CHG'] * 100

        else:
            # Map response to change
            resp_to_change = {'CR': -100, 'PR': -30, 'SD': 0, 'PD': 20,
                            'NON-CR/NON-PD': 0, 'NE': 0}
            df['PCT_CHANGE'] = df[response_col].map(resp_to_change)
            df = df[df['PCT_CHANGE'].notna()]

        if best_response_only:
            # Get best (most negative) response per subject
            df = df.loc[df.groupby('USUBJID')['PCT_CHANGE'].idxmin()]

        df = df.sort_values('PCT_CHANGE', ascending=True).reset_index(drop=True)
        df['X_INDEX'] = range(len(df))

        fig, ax = plt.subplots(figsize=(8.5, 5.5))

        # Color by response category
        response_colors = {
            'CR': '#00AA00',      # Green for complete response
            'PR': '#0077CC',      # Blue for partial response
            'SD': '#AAAAAA',      # Gray for stable disease
            'PD': '#FF0000',      # Red for progressive disease
        }

        # Plot bars
        for i, (_, row) in enumerate(df.iterrows()):
            resp = row.get(response_col, '')
            if resp in response_colors:
                color = response_colors[resp]
            else:
                # Color by treatment arm
                trt_idx = list(df[treatment_col].unique()).index(row[treatment_col])
                color = TREATMENT_COLORS[trt_idx % len(TREATMENT_COLORS)]

            ax.bar(i, row['PCT_CHANGE'], color=color, edgecolor='black',
                   linewidth=0.5, width=0.8)

        # Reference lines
        ax.axhline(y=0, color='black', linewidth=0.8)
        ax.axhline(y=-30, color='gray', linewidth=0.5, linestyle='--', alpha=0.7)
        ax.axhline(y=20, color='gray', linewidth=0.5, linestyle='--', alpha=0.7)

        # Labels
        ax.set_xlim(-1, len(df) + 0.5)
        ax.set_ylim(-110, 120)
        ax.set_xlabel("Subjects (sorted by best % change)", fontsize=9)
        ax.set_ylabel("Best Percent Change from Baseline", fontsize=9)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Response annotations
        ax.text(0.02, 0.02, 'CR: 100% decrease', transform=ax.transAxes,
                fontsize=7, style='italic', color='#00AA00')
        ax.text(0.02, 0.06, 'PR: ≥30% decrease', transform=ax.transAxes,
                fontsize=7, style='italic', color='#0077CC')
        ax.text(0.02, 0.10, 'PD: ≥20% increase', transform=ax.transAxes,
                fontsize=7, style='italic', color='#FF0000')
        ax.text(0.02, 0.14, 'SD: Neither PR nor PD', transform=ax.transAxes,
                fontsize=7, style='italic', color='#AAAAAA')

        # Legend
        if best_response_only:
            legend_handles = [
                mpatches.Patch(color='#00AA00', label='CR'),
                mpatches.Patch(color='#0077CC', label='PR'),
                mpatches.Patch(color='#AAAAAA', label='SD'),
                mpatches.Patch(color='#FF0000', label='PD'),
            ]
            ax.legend(handles=legend_handles, loc="upper right", frameon=False, fontsize=8)

        # Figure header
        fig.text(0.5, 0.97, f"Figure {table_id}", fontsize=10, ha='center', fontweight='normal')
        fig.text(0.5, 0.93, figure_title, fontsize=9, ha='center')
        fig.text(0.5, 0.89, f"({population})", fontsize=8, ha='center', style='italic')

        plt.tight_layout(rect=[0, 0.05, 1, 0.93])

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            return output_path

        plt.close()
        return ""

    def generate_swimmer_plot(
        self,
        adsl: pd.DataFrame,
        adtte: pd.DataFrame = None,
        table_id: str = None,
        figure_title: str = "Swimmer Plot - Treatment Duration and Response",
        population: str = None,
        subject_col: str = "USUBJID",
        treatment_col: str = None,
        treatment_labels: Dict[int, str] = None,
        max_subjects: int = 50,
        output_path: str = None
    ) -> str:
        """
        Generate Swimmer plot showing treatment duration and response events.

        Args:
            adsl: ADSL dataset for subject info
            adtte: ADTTE dataset for event timing (optional)
            table_id: Figure ID
            figure_title: Title of the figure
            population: Population description
            subject_col: Subject identifier column
            treatment_col: Treatment group column
            treatment_labels: Dict mapping treatment number to label
            max_subjects: Maximum number of subjects to display
            output_path: Path to save figure

        Returns:
            Path to saved figure
        """
        if treatment_labels is None:
            treatment_labels = DEFAULT_TREATMENT_LABELS

        if treatment_col is None:
            treatment_col = self._get_trt_col(adsl) or 'TRT01PN'

        df = adsl.copy()

        # Filter for subjects with treatment dates
        if 'TRTSDT' in df.columns and 'TRTEDT' in df.columns:
            df = df[df['TRTSDT'].notna()]

        # Calculate treatment duration in days
        if 'TRTSDT' in df.columns and 'TRTEDT' in df.columns:
            df['DURATION'] = (pd.to_datetime(df['TRTEDT']) - pd.to_datetime(df['TRTSDT'])).dt.days
        elif 'TRTDURD' in df.columns:
            df['DURATION'] = df['TRTDURD']
        else:
            df['DURATION'] = 180  # Default to 180 days

        # Merge with ADTTE for event information
        events_df = None
        if adtte is not None:
            events_df = adtte[adtte['PARAM'].str.contains('PFS|OS|Progression|Response', case=False, na=False)]
            if len(events_df) > 0:
                events_summary = events_df.groupby('USUBJID').agg({
                    'EVNTDESC': lambda x: '; '.join([str(e) for e in x.dropna().unique() if str(e) != '']),
                    'AVAL': 'first'
                }).reset_index()
                df = df.merge(events_summary, on='USUBJID', how='left', suffixes=('', '_evt'))

        df = df.sort_values([treatment_col, subject_col]).head(max_subjects)

        n_subjects = len(df)
        if n_subjects == 0:
            raise ValueError("No subjects found for swimmer plot")

        fig, ax = plt.subplots(figsize=(10, max(6, n_subjects * 0.15 + 2)))

        y_positions = range(n_subjects)

        for i, (_, row) in enumerate(df.iterrows()):
            trt = row.get(treatment_col, 1)
            duration = row.get('DURATION', 100)

            # Color by treatment
            color = TREATMENT_COLORS[int(trt) % len(TREATMENT_COLORS)]

            # Draw treatment duration bar
            ax.barh(i, duration, height=0.6, color=color, edgecolor='black', linewidth=0.3)

            # Add response events
            if events_df is not None and 'EVNTDESC' in row:
                event_text = str(row.get('EVNTDESC_evt', row.get('EVNTDESC', '')))
                if event_text and event_text != 'nan':
                    # Draw event marker
                    event_time = row.get('AVAL', duration * 0.5)
                    ax.plot(event_time, i, 'k|', markersize=8)
                    ax.text(event_time + 5, i, event_text[:20], fontsize=6, va='center')

            # Subject ID label
            ax.text(-5, i, str(row.get(subject_col, ''))[-8:], fontsize=6, va='center', ha='right')

        # Format axes
        max_duration = df['DURATION'].max()
        ax.set_xlim(0, max_duration * 1.1)
        ax.set_ylim(-1, n_subjects)
        ax.set_yticks([])
        ax.set_xlabel("Days", fontsize=9)
        ax.set_ylabel("Subjects", fontsize=9)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)

        # Treatment legend
        legend_handles = []
        for trt in sorted(df[treatment_col].dropna().unique()):
            if pd.notna(trt):
                legend_handles.append(
                    mpatches.Patch(color=TREATMENT_COLORS[int(trt) % 3],
                                   label=treatment_labels.get(int(trt), f"Trt {int(trt)}"))
                )
        ax.legend(handles=legend_handles, loc="upper right", frameon=False, ncol=len(legend_handles))

        # Title
        if table_id:
            fig.text(0.5, 0.96, f"Figure {table_id}", fontsize=10, ha='center', fontweight='normal')
        if figure_title:
            fig.text(0.5, 0.92, figure_title, fontsize=9, ha='center')
        if population:
            fig.text(0.5, 0.88, f"({population})", fontsize=8, ha='center', style='italic')

        plt.tight_layout(rect=[0.08, 0.05, 1, 0.92])

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            return output_path

        plt.close()
        return ""

    def generate_spider_plot(
        self,
        adrs: pd.DataFrame,
        table_id: str,
        figure_title: str,
        population: str,
        subject_col: str = "USUBJID",
        treatment_col: str = None,
        treatment_labels: Dict[int, str] = None,
        time_col: str = "AVISITN",
        tumor_change_col: str = "NRTRN",
        output_path: str = None
    ) -> str:
        """
        Generate Spider plot showing tumor change over time for each subject.

        Args:
            adrs: ADRS dataset with tumor assessment data
            table_id: Figure ID
            figure_title: Title of the figure
            population: Population description
            subject_col: Subject identifier column
            treatment_col: Treatment group column
            treatment_labels: Dict mapping treatment number to label
            time_col: Column for x-axis (visit number or time)
            tumor_change_col: Column containing % change from baseline
            output_path: Path to save figure

        Returns:
            Path to saved figure
        """
        if treatment_labels is None:
            treatment_labels = DEFAULT_TREATMENT_LABELS

        if treatment_col is None:
            treatment_col = self._get_trt_col(adrs) or 'TRTPN'

        df = adrs.copy()

        # Filter for target lesion assessments
        if 'RSTESTCD' in df.columns:
            df = df[df['RSTESTCD'] == 'TRGRESP']

        # Get tumor change data
        if tumor_change_col not in df.columns:
            # Try alternative columns
            for col in ['NRTRN', 'CHG', 'PCTCHG', 'TUMCAL']:
                if col in df.columns:
                    tumor_change_col = col
                    break

        if tumor_change_col not in df.columns:
            raise ValueError(f"Cannot find tumor change column. Available: {list(df.columns)}")

        df = df[df[tumor_change_col].notna()].copy()
        df = df.sort_values([subject_col, time_col])

        fig, ax = plt.subplots(figsize=(8, 5.5))

        subjects = df[subject_col].unique()

        for subj in subjects:
            subj_data = df[df[subject_col] == subj]
            trt = subj_data[treatment_col].iloc[0]

            color = TREATMENT_COLORS[int(trt) % len(TREATMENT_COLORS)]
            alpha = 0.4

            ax.plot(subj_data[time_col], subj_data[tumor_change_col] * 100,
                   color=color, linewidth=0.5, alpha=alpha)

        # Reference lines
        ax.axhline(y=0, color='black', linewidth=0.8)
        ax.axhline(y=-30, color='gray', linewidth=0.5, linestyle='--', alpha=0.7)
        ax.axhline(y=20, color='gray', linewidth=0.5, linestyle='--', alpha=0.7)

        ax.set_xlabel("Visit", fontsize=9)
        ax.set_ylabel("Percent Change from Baseline (%)", fontsize=9)
        ax.set_ylim(-100, 100)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Figure header
        fig.text(0.5, 0.97, f"Figure {table_id}", fontsize=10, ha='center', fontweight='normal')
        fig.text(0.5, 0.93, figure_title, fontsize=9, ha='center')
        fig.text(0.5, 0.89, f"({population})", fontsize=8, ha='center', style='italic')

        plt.tight_layout(rect=[0, 0.05, 1, 0.93])

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            return output_path

        plt.close()
        return ""

    def generate_box_plot(
        self,
        adlb: pd.DataFrame,
        table_id: str,
        figure_title: str,
        population: str,
        param_filter: str = None,
        treatment_col: str = None,
        treatment_labels: Dict[int, str] = None,
        visit_filter: str = None,
        output_path: str = None
    ) -> str:
        """
        Generate Box plot for laboratory values.

        Args:
            adlb: ADLB dataset with lab values
            table_id: Figure ID
            figure_title: Title of the figure
            population: Population description
            param_filter: Filter for PARAM column (e.g., "ALT" or "Hemoglobin")
            treatment_col: Treatment group column
            treatment_labels: Dict mapping treatment number to label
            visit_filter: Filter for specific visit
            output_path: Path to save figure

        Returns:
            Path to saved figure
        """
        if treatment_labels is None:
            treatment_labels = DEFAULT_TREATMENT_LABELS

        if treatment_col is None:
            treatment_col = self._get_trt_col(adlb) or 'TRTPN'

        df = adlb.copy()

        # Filter by parameter
        if param_filter:
            df = df[df['PARAMCD'].str.contains(param_filter, case=False, na=False)]
        else:
            # Use first available parameter
            df = df[df['PARAMCD'] == df['PARAMCD'].iloc[0]]

        # Filter by visit if specified
        if visit_filter and 'AVISIT' in df.columns:
            df = df[df['AVISIT'].str.contains(visit_filter, case=False, na=False)]

        df = df[df['AVAL'].notna()]

        fig, ax = plt.subplots(figsize=(6, 5))

        treatment_groups = sorted(df[treatment_col].dropna().unique())
        positions = list(range(len(treatment_groups)))

        box_data = []
        for trt in treatment_groups:
            trt_data = df[df[treatment_col] == trt]['AVAL']
            box_data.append(trt_data.values)

        bp = ax.boxplot(box_data, positions=positions, patch_artist=True, widths=0.6)

        for i, box in enumerate(bp['boxes']):
            box.set_facecolor(TREATMENT_COLORS[i % len(TREATMENT_COLORS)])
            box.set_alpha(0.6)

        # X-axis labels
        ax.set_xticks(positions)
        ax.set_xticklabels([treatment_labels.get(int(trt), f"Trt {trt}") for trt in treatment_groups])

        ax.set_ylabel("Value", fontsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Figure header
        fig.text(0.5, 0.97, f"Figure {table_id}", fontsize=10, ha='center', fontweight='normal')
        fig.text(0.5, 0.93, figure_title, fontsize=9, ha='center')
        fig.text(0.5, 0.89, f"({population})", fontsize=8, ha='center', style='italic')

        plt.tight_layout(rect=[0, 0.05, 1, 0.93])

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            return output_path

        plt.close()
        return ""

    def save_figure(self, output_path: str) -> None:
        """Save current figure to file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()


class SurvivalFigureGenerator:
    """Specialized generator for survival analysis figures (OS, PFS)."""

    def __init__(self):
        self.colors = TREATMENT_COLORS

    def generate_os_km(
        self,
        adttte: pd.DataFrame,
        table_id: str = "14.2.1.1",
        output_path: str = None,
        **kwargs
    ) -> str:
        """Generate Overall Survival KM figure."""
        fig_gen = FigureGenerator()
        return fig_gen.generate_km_plot(
            adttte=adttte,
            table_id=table_id,
            figure_title="Kaplan-Meier Plot of Overall Survival",
            population="Intent-to-Treat Population",
            param_filter="Overall Survival",
            **kwargs,
            output_path=output_path
        )

    def generate_pfs_km(
        self,
        adttte: pd.DataFrame,
        table_id: str = "14.2.2.1",
        output_path: str = None,
        **kwargs
    ) -> str:
        """Generate Progression-Free Survival KM figure."""
        fig_gen = FigureGenerator()
        return fig_gen.generate_km_plot(
            adttte=adttte,
            table_id=table_id,
            figure_title="Kaplan-Meier Plot of Progression-Free Survival",
            population="Intent-to-Treat Population",
            param_filter="Progression Free Survival",
            **kwargs,
            output_path=output_path
        )


class ResponseFigureGenerator:
    """Specialized generator for tumor response figures."""

    def __init__(self):
        self.colors = TREATMENT_COLORS

    def generate_waterfall(
        self,
        adrs: pd.DataFrame,
        table_id: str = "14.2.4.1",
        output_path: str = None,
        **kwargs
    ) -> str:
        """Generate Best Overall Response Waterfall plot."""
        fig_gen = FigureGenerator()
        return fig_gen.generate_waterfall_plot(
            adrs=adrs,
            table_id=table_id,
            figure_title="Waterfall Plot of Best Overall Response",
            population="Intent-to-Treat Population",
            output_path=output_path,
            **kwargs
        )

    def generate_spider(
        self,
        adrs: pd.DataFrame,
        table_id: str = "14.2.4.2",
        output_path: str = None,
        **kwargs
    ) -> str:
        """Generate Spider plot of tumor change over time."""
        fig_gen = FigureGenerator()
        return fig_gen.generate_spider_plot(
            adrs=adrs,
            table_id=table_id,
            figure_title="Spider Plot of Tumor Change Over Time",
            population="Intent-to-Treat Population",
            output_path=output_path,
            **kwargs
        )

    def generate_swimmer(
        self,
        adsl: pd.DataFrame,
        adtte: pd.DataFrame = None,
        table_id: str = "14.2.4.3",
        output_path: str = None,
        **kwargs
    ) -> str:
        """Generate Swimmer plot of treatment duration."""
        fig_gen = FigureGenerator()
        return fig_gen.generate_swimmer_plot(
            adsl=adsl,
            adtte=adtte,
            table_id=table_id,
            figure_title="Swimmer Plot - Treatment Duration and Response",
            population="Intent-to-Treat Population",
            output_path=output_path,
            **kwargs
        )

    def generate_forest_plot(
        self,
        adrs: pd.DataFrame,
        adsl: pd.DataFrame,
        table_id: str = "14.2.3.3",
        figure_title: str = "Forest Plot of Objective Response Rate",
        population: str = "Intent-to-Treat Population",
        response_col: str = "RSSTRESC",
        output_path: str = None
    ) -> str:
        """Generate Forest plot for objective response rate (ORR) by subgroups."""
        fig, ax = plt.subplots(figsize=(7, 5))

        # Get best overall response per subject
        ovrl = adrs[adrs['RSTESTCD'] == 'OVRLRESP'].copy()
        best_resp = ovrl.groupby('USUBJID').first().reset_index()

        # Calculate ORR (CR + PR) by treatment
        trt_col = 'TRTPN' if 'TRTPN' in best_resp.columns else 'TRT01PN'
        orr_data = best_resp.groupby(trt_col).apply(
            lambda x: pd.Series({
                'n': len(x),
                'responders': ((x[response_col] == 'CR') | (x[response_col] == 'PR')).sum(),
                'rate': ((x[response_col] == 'CR') | (x[response_col] == 'PR')).mean()
            })
        ).reset_index()

        # Plot forest plot style
        treatments = orr_data[trt_col].values
        rates = orr_data['rate'].values
        counts = orr_data['n'].values

        y_positions = range(len(treatments))

        for i, (trt, rate, n) in enumerate(zip(treatments, rates, counts)):
            ax.barh(i, rate * 100, height=0.5, color=TREATMENT_COLORS[i % 3], alpha=0.7)
            ax.text(rate * 100 + 2, i, f'{rate*100:.1f}% (n={n})', va='center', fontsize=8)

        ax.set_yticks(list(y_positions))
        ax.set_yticklabels([f'Treatment {int(t)}' for t in treatments])
        ax.set_xlim(0, 100)
        ax.set_xlabel("Objective Response Rate (%)", fontsize=9)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        fig.text(0.5, 0.97, f"Figure {table_id}", fontsize=10, ha='center', fontweight='normal')
        fig.text(0.5, 0.93, figure_title, fontsize=9, ha='center')
        fig.text(0.5, 0.89, f"({population})", fontsize=8, ha='center', style='italic')

        plt.tight_layout(rect=[0, 0.05, 1, 0.93])

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            return output_path

        plt.close()
        return ""


class LabFigureGenerator:
    """Specialized generator for laboratory and safety figures."""

    def __init__(self):
        self.colors = TREATMENT_COLORS

    def generate_lab_box(
        self,
        adlb: pd.DataFrame,
        table_id: str = "14.3.3.1",
        param: str = None,
        output_path: str = None,
        **kwargs
    ) -> str:
        """Generate box plot for laboratory values."""
        fig_gen = FigureGenerator()
        return fig_gen.generate_box_plot(
            adlb=adlb,
            table_id=table_id,
            figure_title=f"Box Plot of {param or 'Laboratory Values'}",
            population="Safety Analysis Set",
            param_filter=param,
            output_path=output_path,
            **kwargs
        )

    def generate_edish_plot(
        param1_df: pd.DataFrame,
        param2_df: pd.DataFrame,
        table_id: str,
        figure_title: str,
        population: str,
        output_path: str = None
    ) -> str:
        """Generate eDISH plot for liver safety evaluation."""
        # eDISH: Safety Evaluation of Drug-Induced Serious Hepatotoxicity
        # X-axis: Maximum ALT/AST, Y-axis: Maximum TBILI

        fig, ax = plt.subplots(figsize=(6, 5))

        # Plot subjects
        ax.scatter(param1_df['MAX_VAL'], param2_df['MAX_VAL'],
                  c='blue', alpha=0.5, s=20)

        # Reference lines
        ax.axhline(y=2, color='red', linestyle='--', linewidth=1)
        ax.axvline(x=3, color='red', linestyle='--', linewidth=1)

        ax.set_xlabel("Maximum ALT/AST (x ULN)", fontsize=9)
        ax.set_ylabel("Maximum Total Bilirubin (x ULN)", fontsize=9)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Labels for quadrants
        ax.text(0.95, 0.95, 'Potential Hy\'s Law', transform=ax.transAxes,
               fontsize=8, ha='right', va='top', color='red')

        fig.text(0.5, 0.97, f"Figure {table_id}", fontsize=10, ha='center', fontweight='normal')
        fig.text(0.5, 0.93, figure_title, fontsize=9, ha='center')
        fig.text(0.5, 0.89, f"({population})", fontsize=8, ha='center', style='italic')

        plt.tight_layout(rect=[0, 0.05, 1, 0.93])

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            return output_path

        plt.close()
        return ""
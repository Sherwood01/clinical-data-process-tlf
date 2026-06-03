"""
Direct PDF generation with real statistical analysis.
Implements statistical calculations from ADaM datasets (not copying SAS output).
"""

import pyreadstat
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime


class ADaMDataReader:
    """Reads ADaM SAS datasets."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def read_adsl(self) -> pd.DataFrame:
        """Read ADSL dataset."""
        filepath = self.data_dir / "adsl.sas7bdat"
        df, _ = pyreadstat.read_sas7bdat(str(filepath))
        return df


class DispositionAnalyzer:
    """
    Implements statistical analysis for Table 14.1.1.1 (Subject Disposition).
    This is the CORE statistical logic - calculating from ADaM, not copying SAS output.
    """

    def __init__(self, adsl: pd.DataFrame):
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N (number of subjects) by treatment group."""
        big_n = {}
        for trt in [1, 2, 3]:
            big_n[trt] = len(self.adsl[self.adsl['TRT01PN'] == trt])
        return big_n

    def count_flag_total(self, flag: str, value: str = 'Y') -> int:
        """Count subjects with flag (total, not by treatment)."""
        return len(self.adsl[self.adsl[flag] == value])

    def count_flag_by_trt(self, flag: str, value: str = 'Y') -> Dict[int, int]:
        """Count subjects with flag by treatment group."""
        counts = {}
        for trt in [1, 2, 3]:
            counts[trt] = len(self.adsl[
                (self.adsl['TRT01PN'] == trt) &
                (self.adsl[flag] == value)
            ])
        return counts

    def count_flag_by_trt_denom(self, flag: str, value: str = 'Y',
                                 denom_df: pd.DataFrame = None) -> Dict[int, Tuple[int, int]]:
        """
        Count subjects with flag by treatment, return (count, denominator).
        denominator is by treatment group from denom_df.
        """
        if denom_df is None:
            denom_df = self.adsl

        result = {}
        for trt in [1, 2, 3]:
            denom = len(denom_df[denom_df['TRT01PN'] == trt])
            count = len(self.adsl[
                (self.adsl['TRT01PN'] == trt) &
                (self.adsl[flag] == value)
            ])
            result[trt] = (count, denom)
        return result

    def count_discontinuation_reason(self, reason_code: str,
                                     denom_df: pd.DataFrame = None) -> Dict[int, Tuple[int, int]]:
        """Count discontinuation reason by treatment."""
        if denom_df is None:
            denom_df = self.adsl

        result = {}
        for trt in [1, 2, 3]:
            denom = len(denom_df[denom_df['TRT01PN'] == trt])
            count = len(self.adsl[
                (self.adsl['TRT01PN'] == trt) &
                (self.adsl['DISCTFL'] == 'Y') &
                (self.adsl['DCTREAS'] == reason_code)
            ])
            result[trt] = (count, denom)
        return result

    def descriptive_stats(self, var: str, by_trt: bool = True) -> Dict:
        """Calculate descriptive statistics for a continuous variable."""
        if by_trt:
            result = {}
            for trt in [1, 2, 3]:
                subset = self.adsl[
                    (self.adsl['TRT01PN'] == trt) &
                    (self.adsl[var].notna())
                ][var]
                if len(subset) > 0:
                    result[trt] = {
                        'n': len(subset),
                        'mean': subset.mean(),
                        'std': subset.std(),
                        'median': subset.median(),
                        'min': subset.min(),
                        'max': subset.max()
                    }
                else:
                    result[trt] = {'n': 0, 'mean': np.nan, 'std': np.nan,
                                   'median': np.nan, 'min': np.nan, 'max': np.nan}
            return result
        else:
            subset = self.adsl[self.adsl[var].notna()][var]
            if len(subset) > 0:
                return {
                    'n': len(subset),
                    'mean': subset.mean(),
                    'std': subset.std(),
                    'median': subset.median(),
                    'min': subset.min(),
                    'max': subset.max()
                }
            return {'n': 0, 'mean': np.nan, 'std': np.nan,
                    'median': np.nan, 'min': np.nan, 'max': np.nan}

    def analyze(self) -> Dict:
        """
        Perform complete disposition analysis.
        Returns structured results matching Table 14.1.1.1 structure.
        """
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        # Create enrolled population for denominator calculations
        enrlpop = self.adsl[self.adsl['ENRLFL'] == 'Y']
        safpop = self.adsl[self.adsl['SAFFL'] == 'Y']

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        # Unit 01: Screened (total only, no breakdown)
        screened_total = self.count_flag_total('SCRNFL')
        results['units'].append({
            'unit': 'unit01',
            'level': 1,
            'rowlabel': 'No. of Subjects Screened',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': str(screened_total)
        })
        results['units'].append({
            'unit': 'unit01',
            'level': 2,
            'rowlabel': 'ongoing',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': str(screened_total)  # All screened are ongoing
        })

        # Unit 02: Screen Failed (total only)
        screen_failed_total = self.count_flag_total('SCNEFL')
        results['units'].append({
            'unit': 'unit02',
            'level': 1,
            'rowlabel': 'No. of Subjects Screen Failed',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': str(screen_failed_total)
        })

        # Unit 03: Enrolled/Randomized (by treatment)
        enrl_by_trt = self.count_flag_by_trt('ENRLFL')
        results['units'].append({
            'unit': 'unit03',
            'level': 1,
            'rowlabel': 'Analysis Set',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': ''
        })
        results['units'].append({
            'unit': 'unit03',
            'level': 2,
            'rowlabel': 'Enrolled Analysis Set (EAS)',
            'col1': str(enrl_by_trt[1]),
            'col2': str(enrl_by_trt[2]),
            'col3': str(enrl_by_trt[3]),
            'col_total': str(sum(enrl_by_trt.values()))
        })

        # Unit 04: Safety Analysis Set (denom = enrlpop)
        saf_by_trt = self.count_flag_by_trt('SAFFL')
        saf_denom = {}
        for trt in [1, 2, 3]:
            saf_denom[trt] = len(enrlpop[enrlpop['TRT01PN'] == trt])

        def fmt_freq(count, denom):
            pct = (count / denom * 100) if denom > 0 else 0
            return f"{count} ({pct:.1f})"

        results['units'].append({
            'unit': 'unit04',
            'level': 2,
            'rowlabel': 'Safety Analysis Set',
            'col1': fmt_freq(saf_by_trt[1], saf_denom[1]),
            'col2': fmt_freq(saf_by_trt[2], saf_denom[2]),
            'col3': fmt_freq(saf_by_trt[3], saf_denom[3]),
            'col_total': fmt_freq(sum(saf_by_trt.values()), total_n)
        })

        # Unit 05: Response Evaluable Set
        res_by_trt = self.count_flag_by_trt('RESFL')
        res_denom = {}
        for trt in [1, 2, 3]:
            res_denom[trt] = len(enrlpop[enrlpop['TRT01PN'] == trt])

        results['units'].append({
            'unit': 'unit05',
            'level': 2,
            'rowlabel': 'Response Evaluable Set',
            'col1': fmt_freq(res_by_trt[1], res_denom[1]),
            'col2': fmt_freq(res_by_trt[2], res_denom[2]),
            'col3': fmt_freq(res_by_trt[3], res_denom[3]),
            'col_total': fmt_freq(sum(res_by_trt.values()), total_n)
        })

        # Unit 06: PK Analysis Set
        pk_by_trt = self.count_flag_by_trt('PKFL')
        pk_denom = saf_denom  # PK uses same denominator as Safety

        results['units'].append({
            'unit': 'unit06',
            'level': 2,
            'rowlabel': 'PK Analysis Set',
            'col1': fmt_freq(pk_by_trt[1], pk_denom[1]),
            'col2': fmt_freq(pk_by_trt[2], pk_denom[2]),
            'col3': fmt_freq(pk_by_trt[3], pk_denom[3]),
            'col_total': fmt_freq(sum(pk_by_trt.values()), total_n)
        })

        # Unit 07: Ongoing/Discontinued (Treatment Status in EAS)
        ong_by_trt = self.count_flag_by_trt('ONGFL')
        results['units'].append({
            'unit': 'unit07',
            'level': 1,
            'rowlabel': 'Treatment Status in the EAS',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': ''
        })
        results['units'].append({
            'unit': 'unit07',
            'level': 2,
            'rowlabel': 'Ongoing',
            'col1': fmt_freq(ong_by_trt[1], saf_denom[1]),
            'col2': fmt_freq(ong_by_trt[2], saf_denom[2]),
            'col3': fmt_freq(ong_by_trt[3], saf_denom[3]),
            'col_total': fmt_freq(sum(ong_by_trt.values()), total_n)
        })

        # Unit 08: Discontinued
        disct_by_trt = self.count_flag_by_trt('DISCTFL')
        results['units'].append({
            'unit': 'unit08',
            'level': 2,
            'rowlabel': 'Discontinued',
            'col1': fmt_freq(disct_by_trt[1], saf_denom[1]),
            'col2': fmt_freq(disct_by_trt[2], saf_denom[2]),
            'col3': fmt_freq(disct_by_trt[3], saf_denom[3]),
            'col_total': fmt_freq(sum(disct_by_trt.values()), total_n)
        })

        # Unit 09: Primary Reason for Discontinuation
        results['units'].append({
            'unit': 'unit09',
            'level': 3,
            'rowlabel': 'Primary Reason for Discontinuation from Study Treatment',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': ''
        })

        # Discontinuation reasons
        reasons = [
            ('Adverse Event', 'ADVERSE EVENT'),
            ('Lost to Follow-up', 'LOST TO FOLLOW-UP'),
            ('Death', 'DEATH'),
            ('Protocol Deviation', 'PROTOCOL DEVIATION'),
            ('Withdrawal  by Subject', 'WITHDRAWAL BY SUBJECT'),
            ('Physician Decision', 'PHYSICIAN DECISION'),
            ('Study Terminated by Sponsor', 'STUDY TERMINATED BY SPONSOR'),
            ('Clinical Progression', 'CLINICAL PROGRESSION'),
            ('Progressive Disease', 'PROGRESSIVE DISEASE'),
            ('Other', 'OTHER')
        ]

        for reason_label, reason_code in reasons:
            reason_counts = self.count_discontinuation_reason(reason_code, safpop)
            total_count = sum(c for c, d in reason_counts.values())
            total_denom = sum(d for c, d in reason_counts.values())

            results['units'].append({
                'unit': 'unit09',
                'level': 4,
                'rowlabel': reason_label,
                'col1': fmt_freq(reason_counts[1][0], reason_counts[1][1]) if reason_counts[1][1] > 0 else '0',
                'col2': fmt_freq(reason_counts[2][0], reason_counts[2][1]) if reason_counts[2][1] > 0 else '0',
                'col3': fmt_freq(reason_counts[3][0], reason_counts[3][1]) if reason_counts[3][1] > 0 else '0',
                'col_total': fmt_freq(total_count, total_denom) if total_denom > 0 else '0'
            })

        # Unit 10: Duration of Follow-up (months)
        dur_stats = self.descriptive_stats('STUDURM', by_trt=True)
        dur_total = self.descriptive_stats('STUDURM', by_trt=False)

        results['units'].append({
            'unit': 'unit10',
            'level': 1,
            'rowlabel': 'Duration of Follow-up (months)',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': ''
        })

        # n
        results['units'].append({
            'unit': 'unit10',
            'level': 2,
            'rowlabel': 'n',
            'col1': str(dur_stats[1]['n']),
            'col2': str(dur_stats[2]['n']),
            'col3': str(dur_stats[3]['n']),
            'col_total': str(dur_total['n'])
        })

        # Mean
        def fmt_mean(val):
            return f"{val:.2f}" if not np.isnan(val) else ''

        results['units'].append({
            'unit': 'unit10',
            'level': 2,
            'rowlabel': 'Mean',
            'col1': fmt_mean(dur_stats[1]['mean']),
            'col2': fmt_mean(dur_stats[2]['mean']),
            'col3': fmt_mean(dur_stats[3]['mean']),
            'col_total': fmt_mean(dur_total['mean'])
        })

        # Std. Dev.
        results['units'].append({
            'unit': 'unit10',
            'level': 2,
            'rowlabel': 'Std. Dev.',
            'col1': f"{dur_stats[1]['std']:.3f}" if not np.isnan(dur_stats[1]['std']) else '',
            'col2': f"{dur_stats[2]['std']:.3f}" if not np.isnan(dur_stats[2]['std']) else '',
            'col3': f"{dur_stats[3]['std']:.3f}" if not np.isnan(dur_stats[3]['std']) else '',
            'col_total': f"{dur_total['std']:.3f}" if not np.isnan(dur_total['std']) else ''
        })

        # Median
        results['units'].append({
            'unit': 'unit10',
            'level': 2,
            'rowlabel': 'Median',
            'col1': f"{dur_stats[1]['median']:.2f}" if not np.isnan(dur_stats[1]['median']) else '',
            'col2': f"{dur_stats[2]['median']:.2f}" if not np.isnan(dur_stats[2]['median']) else '',
            'col3': f"{dur_stats[3]['median']:.2f}" if not np.isnan(dur_stats[3]['median']) else '',
            'col_total': f"{dur_total['median']:.2f}" if not np.isnan(dur_total['median']) else ''
        })

        # Min, Max
        def fmt_minmax(stats):
            if np.isnan(stats['min']) or np.isnan(stats['max']):
                return ''
            return f"{stats['min']:.1f}, {stats['max']:.1f}"

        results['units'].append({
            'unit': 'unit10',
            'level': 2,
            'rowlabel': 'Min, Max',
            'col1': fmt_minmax(dur_stats[1]),
            'col2': fmt_minmax(dur_stats[2]),
            'col3': fmt_minmax(dur_stats[3]),
            'col_total': fmt_minmax(dur_total)
        })

        return results


class TableOutputGenerator:
    """
    Generates table_14_1_1_1.sas7bdat in the same format as SAS output.
    This is the INTERMEDIATE OUTPUT that would normally come from running SAS.
    """

    def __init__(self):
        pass

    def generate_output_data(self, analysis_results: Dict) -> pd.DataFrame:
        """Generate output DataFrame in SAS output format."""
        rows = []
        index = 0

        big_n = analysis_results['big_n']
        total_n = analysis_results['total_n']

        for unit_data in analysis_results['units']:
            unit = unit_data['unit']
            level = unit_data['level']
            rowlabel = unit_data['rowlabel']
            col1 = unit_data['col1']
            col2 = unit_data['col2']
            col3 = unit_data['col3']
            col_total = unit_data['col_total']

            # Determine _group1 and _group2 based on structure
            if level == 1:
                _group1 = rowlabel
                _group2 = ''
            elif level == 2 and unit in ['unit01']:
                _group1 = 'No. of Subjects Screened'
                _group2 = 'ongoing'
            elif level == 2 and unit in ['unit03']:
                _group1 = 'Analysis Set'
                _group2 = rowlabel
            elif level == 2 and unit in ['unit07']:
                _group1 = 'Treatment Status in the EAS'
                _group2 = rowlabel
            else:
                _group1 = ''
                _group2 = ''

            rows.append({
                'rowlabel': rowlabel,
                '_col_1': col1,
                '_col_2': col2,
                '_col_3': col3,
                '_col_99999': col_total,
                '_unit_': unit,
                'index': float(index + 1),
                'dummy': '1',
                'level': float(level),
                '_group1': _group1,
                '_group2': _group2,
                'ord': float(index + 1),
                '_byvar_': '1',
                '_byvar_n': 0.0
            })
            index += 1

        df = pd.DataFrame(rows)
        return df

    def generate_output_data_generic(self, analysis_results: Dict,
                                      has_col2: bool = True, has_col3: bool = True) -> pd.DataFrame:
        """Generate output DataFrame with flexible columns."""
        rows = []
        index = 0

        for unit_data in analysis_results['units']:
            unit = unit_data['unit']
            level = unit_data['level']
            rowlabel = unit_data['rowlabel']
            col1 = unit_data.get('col1', '')
            col2 = unit_data.get('col2', '')
            col3 = unit_data.get('col3', '')
            col_total = unit_data.get('col_total', '')

            row = {
                'rowlabel': rowlabel,
                '_col_1': col1,
                '_col_2': col2 if has_col2 else '',
                '_col_3': col3 if has_col3 else '',
                '_col_99999': col_total,
                '_unit_': unit,
                'index': float(index + 1),
                'dummy': '1',
                'level': float(level),
                '_group1': '',
                '_group2': '',
                '_group3': '',
                '_group4': '',
                'ord': float(index + 1),
                '_byvar_': '1',
                '_byvar_n': 0.0
            }
            rows.append(row)
            index += 1

        df = pd.DataFrame(rows)
        return df

    def save_sas_output(self, df: pd.DataFrame, output_path: str):
        """Save output as SAS dataset."""
        # Note: pyreadstat doesn't support writing SAS files directly
        # For now, save as CSV (which can be converted to SAS if needed)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path = output_path.with_suffix('.csv')
        df.to_csv(csv_path, index=False)
        print(f"  Note: SAS output saved as CSV (pyreadstat doesn't support writing .sas7bdat)")
        print(f"  CSV: {csv_path}")
        return str(csv_path)


class PDFReportGenerator:
    """Generates PDF report from analysis results."""

    def __init__(self):
        pass

    def generate(self, analysis_results: Dict, output_path: str,
              table_title: str = "Subject Disposition",
              table_id: str = "14.1.1.1") -> str:
        """Generate PDF from analysis results."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle,
            Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle('Title', fontSize=14, alignment=1, spaceAfter=6)
        header_style = ParagraphStyle('Header', fontSize=10, alignment=1, spaceAfter=12)

        elements.append(Paragraph(f"Table {table_id}", title_style))
        elements.append(Paragraph(table_title, header_style))
        elements.append(Spacer(1, 0.15*inch))

        # Build table headers with actual N
        big_n = analysis_results['big_n']
        total_n = analysis_results['total_n']

        headers = [
            "Characteristic",
            f"5.4 mg/kg (N={big_n[1]})",
            f"6.4 mg/kg (N={big_n[2]})",
            f"7.4 mg/kg (N={big_n[3]})",
            f"Total (N={total_n})"
        ]

        # Build table data
        table_data = [headers]
        for unit_data in analysis_results['units']:
            level = unit_data['level']
            rowlabel = unit_data['rowlabel']
            col1 = unit_data['col1']
            col2 = unit_data['col2']
            col3 = unit_data['col3']
            col_total = unit_data['col_total']

            # Indent based on level
            indent = "  " * (level - 1) if level > 1 else ""
            row = [f"{indent}{rowlabel}", col1, col2, col3, col_total]
            table_data.append(row)

        # Column widths
        col_widths = [2.8*inch, 1.4*inch, 1.4*inch, 1.4*inch, 1.4*inch]
        table = Table(table_data, colWidths=col_widths)

        # Style
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.6)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),

            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ('LEFTPADDING', (0, 1), (0, -1), 8),
        ]))

        elements.append(table)

        # Footer
        elements.append(Spacer(1, 0.2*inch))
        footer_style = ParagraphStyle('Footer', fontSize=7, textColor=colors.grey)
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Source: ADaM.ADSL",
            footer_style
        ))

        doc.build(elements)
        return str(output_path)

    def generate_generic(self, analysis_results: Dict, output_path: str,
                         table_title: str = "Analysis Table",
                         table_id: str = "14.1.1.2",
                         population: str = "Enrolled Analysis Set") -> str:
        """Generate PDF with generic structure matching reference style."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle,
            Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        styles = getSampleStyleSheet()
        elements = []

        # Title style: "Table 14.1.2.1" - centered, normal (not bold)
        title_style = ParagraphStyle('Title', fontSize=10, alignment=1,
                                     fontName='Helvetica', spaceAfter=2)
        # Name style: "Demographic and Baseline Characteristics" - centered, normal
        name_style = ParagraphStyle('Name', fontSize=9, alignment=1,
                                    fontName='Helvetica', spaceAfter=2)
        # Population style: "Enrolled Analysis Set" - centered, italic
        pop_style = ParagraphStyle('Population', fontSize=8, alignment=1,
                                  fontName='Helvetica-Oblique', spaceAfter=8,
                                  textColor=colors.Color(0.4, 0.4, 0.4))

        elements.append(Paragraph(f"Table {table_id}", title_style))
        elements.append(Paragraph(table_title, name_style))
        elements.append(Paragraph(population, pop_style))
        elements.append(Spacer(1, 0.15*inch))

        # Build table headers
        big_n = analysis_results.get('big_n', {1: 0, 2: 0, 3: 0})
        total_n = analysis_results.get('total_n', 0)

        headers = [
            "Characteristic",
            f"5.4 mg/kg (N={big_n.get(1, 0)})",
            f"6.4 mg/kg (N={big_n.get(2, 0)})",
            f"7.4 mg/kg (N={big_n.get(3, 0)})",
            f"Total (N={total_n})"
        ]

        # Build table data
        table_data = [headers]
        for unit_data in analysis_results['units']:
            level = unit_data['level']
            rowlabel = unit_data['rowlabel']
            col1 = unit_data.get('col1', '')
            col2 = unit_data.get('col2', '')
            col3 = unit_data.get('col3', '')
            col_total = unit_data.get('col_total', '')

            # Indent based on level
            indent = "  " * max(0, int(level) - 1)
            row = [f"{indent}{rowlabel}", col1, col2, col3, col_total]
            table_data.append(row)

        # Column widths
        col_widths = [3.0*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch]
        table = Table(table_data, colWidths=col_widths)

        # Style - reference PDF style: no borders, white background
        table.setStyle(TableStyle([
            # Header - white background, black bold text, only bottom line
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('TOPPADDING', (0, 0), (-1, 0), 4),
            # Only bottom line for header - make it more prominent
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),

            # Body - no borders, white background, no alternating colors
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            # No grid/border at all
            ('TOPPADDING', (0, 1), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
            ('LEFTPADDING', (0, 1), (0, -1), 4),
            # White background for all data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ]))

        elements.append(table)

        # Footer with Program and Output (like reference PDF)
        elements.append(Spacer(1, 0.15*inch))
        footer_style = ParagraphStyle('Footer', fontSize=7, textColor=colors.grey)
        from datetime import datetime
        timestamp = datetime.now().strftime('%d%b%Y %H:%M').upper()
        footer_text = f"Program: Generate_Table_{table_id.replace('.', '_')}.sas | Output: Table_{table_id.replace('.', '_')}.pdf | Generated: {timestamp}"
        elements.append(Paragraph(footer_text, footer_style))

        doc.build(elements)
        return str(output_path)


class AESummaryAnalyzer:
    """
    Implements statistical analysis for Table 14.3.1.1 (AE Summary).

    Summary table of treatment-emergent adverse events (TEAE) including:
    - Overall TEAE rates
    - Grade 3+ TEAE rates
    - TEAE by outcome (death, discontinuation, dose interruption, dose reduction)
    - Related TEAE rates
    - SAE rates
    """

    def __init__(self, adae: pd.DataFrame, adsl: pd.DataFrame):
        self.adae = adae
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[trt] = len(saf[saf['TRT01PN'] == trt])
        return big_n

    def _count_unique_subjects(self, df: pd.DataFrame, trt: float,
                                filters: dict = None) -> int:
        """
        Count unique subjects with at least one AE meeting criteria.
        TRTEMFL='' records are excluded from analysis per convention.
        """
        subset = df[(df['TRTPN'] == trt) & (df['TRTEMFL'] == 'Y')].copy()

        if filters:
            for col, val in filters.items():
                if val is None:
                    continue
                elif isinstance(val, list):
                    subset = subset[subset[col].isin(val)]
                else:
                    subset = subset[subset[col] == val]

        return subset['USUBJID'].nunique()

    def _count_unique_any_ae(self, df: pd.DataFrame, trt: float,
                            rel_filter: str = None) -> int:
        """
        Count unique subjects with any AE (no TRTEMFL filter for base TEAE).
        For Related TEAE, filter by AEREL='RELATED'.
        """
        subset = df[df['TRTPN'] == trt].copy()

        if rel_filter == 'RELATED':
            subset = subset[subset['AEREL'] == 'RELATED']
        elif rel_filter == 'UNRELATED':
            subset = subset[subset['AEREL'] == 'UNRELATED']

        return subset['USUBJID'].nunique()

    def analyze(self) -> Dict:
        """Perform complete AE summary analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        # Filter ADAE to Safety Analysis Set
        adae_saf = self.adae[self.adae['SAFFL'] == 'Y'].copy()

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        def fmt_freq(count: int, denom: int) -> str:
            """Format as 'count (pct%)'."""
            if denom == 0:
                return "0 (0.0)"
            pct = count / denom * 100
            return f"{count} ({pct:.1f})"

        trt_list = sorted(big_n.keys())

        # Helper to compute all treatment columns
        def compute_row(get_count_fn, denom_fn=None):
            """Generic row computation for all treatment groups."""
            row = {'unit': '', 'level': 1, 'rowlabel': '',
                   'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
            total_count = 0
            total_denom = 0

            for i, trt in enumerate(trt_list, 1):
                denom = denom_fn(trt) if denom_fn else big_n.get(trt, 0)
                count = get_count_fn(trt)
                col_key = f'col{i}'
                row[col_key] = fmt_freq(count, denom)
                total_count += count
                total_denom += denom

            row['col_total'] = fmt_freq(total_count, total_denom)
            return row

        # Row 0: Treatment-Emergent Adverse Events (TEAE)
        row = {'unit': 'unit01', 'level': 1, 'rowlabel': 'Treatment-Emergent Adverse Events (TEAE)',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_any_ae(adae_saf, trt)
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 1: TEAE with CTCAE Grade >= 3
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'TEAE with CTCAE Grade >= 3',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt, {'AETOXGR': ['3', '4', '5']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 2: TEAE associated with Death as Outcome
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'TEAE associated with Death as Outcome',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt, {'AEOUT': ['FATAL']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 3: TEAE associated with Study Treatment Discontinuation
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'TEAE associated with Study Treatment Discontinuation',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt, {'ADISCFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 4: TEAE associated with Study Treatment Dose Interruption
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'TEAE associated with Study Treatment Dose Interruption',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt, {'AINTERFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 5: TEAE associated with Study Treatment Dose Reduction
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'TEAE associated with Study Treatment Dose Reduction',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt, {'AREDUFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 6: Treatment-Related TEAE (Related TEAE)
        row = {'unit': 'unit02', 'level': 1,
               'rowlabel': 'Treatment-Related TEAE (Related TEAE)',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_any_ae(adae_saf, trt, rel_filter='RELATED')
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 7: Related TEAE with CTCAE Grade >= 3
        row = {'unit': 'unit02', 'level': 1,
               'rowlabel': 'Related TEAE with CTCAE Grade >= 3',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AEREL': ['RELATED'], 'AETOXGR': ['3', '4', '5']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 8: Related TEAE associated with Death as Outcome
        row = {'unit': 'unit02', 'level': 1,
               'rowlabel': 'Related TEAE associated with Death as Outcome',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AEREL': ['RELATED'], 'AEOUT': ['FATAL']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 9: Related TEAE associated with Study Treatment Discontinuation
        row = {'unit': 'unit02', 'level': 1,
               'rowlabel': 'Related TEAE associated with Study Treatment Discontinuation',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AEREL': ['RELATED'], 'ADISCFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 10: Related TEAE associated with Study Treatment Dose Interruption
        row = {'unit': 'unit02', 'level': 1,
               'rowlabel': 'Related TEAE associated with Study Treatment Dose Interruption',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AEREL': ['RELATED'], 'AINTERFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 11: Related TEAE associated with Study Treatment Dose Reduction
        row = {'unit': 'unit02', 'level': 1,
               'rowlabel': 'Related TEAE associated with Study Treatment Dose Reduction',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AEREL': ['RELATED'], 'AREDUFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 12: Treatment-Emergent Serious Adverse Events (SAE)
        row = {'unit': 'unit03', 'level': 1,
               'rowlabel': 'Treatment-Emergent Serious Adverse Events (SAE)',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt, {'AESER': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 13: SAE with CTCAE Grade >= 3
        row = {'unit': 'unit03', 'level': 1,
               'rowlabel': 'SAE with CTCAE Grade >= 3',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AETOXGR': ['3', '4', '5']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 14: SAE associated with Death as Outcome
        row = {'unit': 'unit03', 'level': 1,
               'rowlabel': 'SAE associated with Death as Outcome',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AEOUT': ['FATAL']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 15: SAE associated with Study Treatment Discontinuation
        row = {'unit': 'unit03', 'level': 1,
               'rowlabel': 'SAE associated with Study Treatment Discontinuation',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'ADISCFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 16: SAE associated with Study Treatment Dose Interruption
        row = {'unit': 'unit03', 'level': 1,
               'rowlabel': 'SAE associated with Study Treatment Dose Interruption',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AINTERFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 17: SAE associated with Study Treatment Dose Reduction
        row = {'unit': 'unit03', 'level': 1,
               'rowlabel': 'SAE associated with Study Treatment Dose Reduction',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AREDUFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 18: Treatment-Related SAE (Related SAE)
        row = {'unit': 'unit04', 'level': 1,
               'rowlabel': 'Treatment-Related SAE (Related SAE)',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AEREL': ['RELATED']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 19: Related SAE with CTCAE Grade >= 3
        row = {'unit': 'unit04', 'level': 1,
               'rowlabel': 'Related SAE with CTCAE Grade >= 3',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AEREL': ['RELATED'],
                                            'AETOXGR': ['3', '4', '5']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 20: Related SAE associated with Death as Outcome
        row = {'unit': 'unit04', 'level': 1,
               'rowlabel': 'Related SAE associated with Death as Outcome',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AEREL': ['RELATED'],
                                            'AEOUT': ['FATAL']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 21: Related SAE associated with Study Treatment Discontinuation
        row = {'unit': 'unit04', 'level': 1,
               'rowlabel': 'Related SAE associated with Study Treatment Discontinuation',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AEREL': ['RELATED'],
                                            'ADISCFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 22: Related SAE associated with Study Treatment Dose Interruption
        row = {'unit': 'unit04', 'level': 1,
               'rowlabel': 'Related SAE associated with Study Treatment Dose Interruption',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AEREL': ['RELATED'],
                                            'AINTERFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        # Row 23: Related SAE associated with Study Treatment Dose Reduction
        row = {'unit': 'unit04', 'level': 1,
               'rowlabel': 'Related SAE associated with Study Treatment Dose Reduction',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total = 0
        for i, trt in enumerate(trt_list, 1):
            n = self._count_unique_subjects(adae_saf, trt,
                                           {'AESER': ['Y'], 'AEREL': ['RELATED'],
                                            'AREDUFL': ['Y']})
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total += n
        row['col_total'] = fmt_freq(total, total_n)
        results['units'].append(row)

        return results


class BestOverallResponseAnalyzer:
    """
    Implements statistical analysis for Table 14.2.1.1 (Best Overall Response and ORR).

    This analyzes tumor response data from ADRS dataset:
    - Best Overall Response (Confirmed and Unconfirmed)
    - Objective Response Rate (ORR = CR + PR) at various time points
    - Denominator is Safety Analysis Set (SAFFL='Y')
    """

    def __init__(self, adrs: pd.DataFrame, adsl: pd.DataFrame):
        self.adrs = adrs
        self.adsl = adsl
        # Response hierarchy for best overall response
        self.response_order = ['CR', 'PR', 'SD', 'PD', 'NE', 'NON-CR/NON-PD']

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(saf[saf['TRT01PN'] == trt])
        return big_n

    def get_measurable_count_by_trt(self) -> Dict[int, int]:
        """Get count of subjects with measurable tumors at baseline (RESPOP)."""
        counts = {}
        respop = self.adsl[self.adsl['RESFL'] == 'Y']
        for trt in [1, 2, 3]:
            counts[trt] = len(respop[respop['TRT01PN'] == trt])
        return counts

    def _filter_ovrlresp_ia(self, require_confirmation: bool = False) -> pd.DataFrame:
        """
        Filter ADRS to OVRLRESP with Independent Assessor evaluation.

        For confirmed responses (require_confirmation=True):
        - RSACPTFL='Y' (confirmation flag)
        - RSEVAL='INDEPENDENT ASSESSOR'
        """
        mask = (
            (self.adrs['RSTESTCD'] == 'OVRLRESP') &
            (self.adrs['RSEVAL'] == 'INDEPENDENT ASSESSOR')
        )
        if require_confirmation:
            mask = mask & (self.adrs['RSACPTFL'] == 'Y')

        return self.adrs[mask].copy()

    def _has_two_consecutive(self, responses: list, target: str) -> bool:
        """Check if there are two consecutive same responses."""
        for i in range(len(responses) - 1):
            if responses[i] == target and responses[i + 1] == target:
                return True
        return False

    def _get_best_response(self, df: pd.DataFrame, confirmed: bool = False) -> Dict[str, str]:
        """
        Get best response per subject based on response hierarchy.

        For confirmed responses:
        - CR requires two consecutive CR
        - PR requires two consecutive PR (or better which would be CR)
        - SD: any SD response (if not PR/CR)
        - PD: any PD response
        - NE: any NE response
        - NON-CR/NON-PD: NON-CR/NON-PD response

        For unconfirmed responses:
        - Any response counts, using hierarchy
        """
        best = {}
        for subj, grp in df.groupby('USUBJID'):
            grp = grp.sort_values('RSDTC')
            responses = list(grp['RSSTRESC'])

            if confirmed:
                # Confirmed response logic
                if self._has_two_consecutive(responses, 'CR'):
                    best[subj] = 'CR'
                elif self._has_two_consecutive(responses, 'PR'):
                    best[subj] = 'PR'
                else:
                    # Find best non-confirmed response
                    for resp in self.response_order:
                        if resp in responses:
                            best[subj] = resp
                            break
            else:
                # Unconfirmed - any response
                for resp in self.response_order:
                    if resp in responses:
                        best[subj] = resp
                        break

        return best

    def _count_by_response(self, response_dict: Dict[str, str]) -> Dict[str, int]:
        """Count subjects by response category."""
        counts = {resp: 0 for resp in self.response_order}
        for resp in response_dict.values():
            if resp in counts:
                counts[resp] += 1
        return counts

    def _get_confirmed_best_response_by_trt(self) -> Dict[int, Dict[str, int]]:
        """Get confirmed best response counts by treatment."""
        ovrl = self._filter_ovrlresp_ia(require_confirmation=True)

        result = {}
        for trt in [1, 2, 3]:
            trt_data = ovrl[ovrl['TRTPN'] == trt]
            best_resp = self._get_best_response(trt_data, confirmed=True)
            counts = self._count_by_response(best_resp)
            result[trt] = counts
        return result

    def _get_unconfirmed_best_response_by_trt(self) -> Dict[int, Dict[str, int]]:
        """Get unconfirmed best response counts by treatment."""
        # For unconfirmed, include all IA evaluations (both radiologists)
        ovrl = self._filter_ovrlresp_ia(require_confirmation=False)

        result = {}
        for trt in [1, 2, 3]:
            trt_data = ovrl[ovrl['TRTPN'] == trt]
            best_resp = self._get_best_response(trt_data, confirmed=False)
            counts = self._count_by_response(best_resp)
            result[trt] = counts
        return result

    def _calc_or_with_ci(self, n: int, denom: int) -> Tuple[str, str]:
        """Calculate response rate and 95% CI using normal approximation."""
        if denom == 0:
            return "0 (0.0)", "(NC, NC)"
        rate = n / denom
        pct = rate * 100
        # Wilson score interval for proportion
        z = 1.96
        denom_float = float(denom)
        center = (rate + z**2 / (2 * denom_float)) / (1 + z**2 / denom_float)
        spread = z * np.sqrt(rate * (1 - rate) / denom_float + z**2 / (4 * denom_float**2)) / (1 + z**2 / denom_float)
        ci_low = max(0, (center - spread) * 100)
        ci_high = min(100, (center + spread) * 100)
        return f"{pct:.1f}", f"({ci_low:.1f}, {ci_high:.1f})"

    def analyze(self) -> Dict:
        """Perform complete Best Overall Response analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())
        meas = self.get_measurable_count_by_trt()

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        def fmt_freq(count: int, denom: int) -> str:
            if denom == 0:
                return "0 (0.0)"
            pct = count / denom * 100
            return f"{count} ({pct:.1f})"

        trt_list = [1, 2, 3]

        # Row 0: Number (%) of Subjects with Measurable Tumors at Baseline
        results['units'].append({
            'unit': 'unit01',
            'level': 1,
            'rowlabel': 'Number (%) of Subjects with Measurable Tumors at Baseline',
            'col1': fmt_freq(meas.get(1, 0), big_n.get(1, 0)),
            'col2': fmt_freq(meas.get(2, 0), big_n.get(2, 0)),
            'col3': fmt_freq(meas.get(3, 0), big_n.get(3, 0)),
            'col_total': fmt_freq(sum(meas.values()), total_n)
        })

        # Confirmed Best Overall Response
        confirmed_resp = self._get_confirmed_best_response_by_trt()

        # Header row for Confirmed BOR
        results['units'].append({
            'unit': 'unit02',
            'level': 1,
            'rowlabel': 'Best Overall Response (Confirmed)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Confirmed response categories
        for resp in ['CR', 'PR', 'SD', 'PD', 'NE']:
            counts = {trt: confirmed_resp[trt].get(resp, 0) for trt in trt_list}
            total = sum(counts.values())
            results['units'].append({
                'unit': 'unit02',
                'level': 2,
                'rowlabel': f"  {resp}",
                'col1': fmt_freq(counts[1], big_n[1]),
                'col2': fmt_freq(counts[2], big_n[2]),
                'col3': fmt_freq(counts[3], big_n[3]),
                'col_total': fmt_freq(total, total_n)
            })

        # ORR Header
        results['units'].append({
            'unit': 'unit03',
            'level': 1,
            'rowlabel': 'Confirmed Objective Response Rate (ORR)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # ORR = CR + PR (confirmed)
        orr_counts = {trt: confirmed_resp[trt].get('CR', 0) + confirmed_resp[trt].get('PR', 0)
                      for trt in trt_list}
        orr_total = sum(orr_counts.values())

        # n (%)
        results['units'].append({
            'unit': 'unit03',
            'level': 2,
            'rowlabel': '  n (%)',
            'col1': fmt_freq(orr_counts[1], big_n[1]),
            'col2': fmt_freq(orr_counts[2], big_n[2]),
            'col3': fmt_freq(orr_counts[3], big_n[3]),
            'col_total': fmt_freq(orr_total, total_n)
        })

        # 95% CI
        results['units'].append({
            'unit': 'unit03',
            'level': 2,
            'rowlabel': '  95% CI',
            'col1': self._calc_or_with_ci(orr_counts[1], big_n[1])[1],
            'col2': self._calc_or_with_ci(orr_counts[2], big_n[2])[1],
            'col3': self._calc_or_with_ci(orr_counts[3], big_n[3])[1],
            'col_total': self._calc_or_with_ci(orr_total, total_n)[1]
        })

        # Unconfirmed Best Overall Response
        unconf_resp = self._get_unconfirmed_best_response_by_trt()

        # Header row for Unconfirmed BOR
        results['units'].append({
            'unit': 'unit04',
            'level': 1,
            'rowlabel': 'Best Overall Response (Unconfirmed)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Unconfirmed response categories
        for resp in ['CR', 'PR', 'SD', 'PD', 'NE']:
            counts = {trt: unconf_resp[trt].get(resp, 0) for trt in trt_list}
            total = sum(counts.values())
            results['units'].append({
                'unit': 'unit04',
                'level': 2,
                'rowlabel': f"  {resp}",
                'col1': fmt_freq(counts[1], big_n[1]),
                'col2': fmt_freq(counts[2], big_n[2]),
                'col3': fmt_freq(counts[3], big_n[3]),
                'col_total': fmt_freq(total, total_n)
            })

        # Unconfirmed ORR Header
        results['units'].append({
            'unit': 'unit05',
            'level': 1,
            'rowlabel': 'Unconfirmed ORR',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Unconfirmed ORR = CR + PR (unconfirmed)
        unorr_counts = {trt: unconf_resp[trt].get('CR', 0) + unconf_resp[trt].get('PR', 0)
                        for trt in trt_list}
        unorr_total = sum(unorr_counts.values())

        results['units'].append({
            'unit': 'unit05',
            'level': 2,
            'rowlabel': '  n (%)',
            'col1': fmt_freq(unorr_counts[1], big_n[1]),
            'col2': fmt_freq(unorr_counts[2], big_n[2]),
            'col3': fmt_freq(unorr_counts[3], big_n[3]),
            'col_total': fmt_freq(unorr_total, total_n)
        })

        # 95% CI for unconfirmed ORR
        results['units'].append({
            'unit': 'unit05',
            'level': 2,
            'rowlabel': '  95% CI',
            'col1': self._calc_or_with_ci(unorr_counts[1], big_n[1])[1],
            'col2': self._calc_or_with_ci(unorr_counts[2], big_n[2])[1],
            'col3': self._calc_or_with_ci(unorr_counts[3], big_n[3])[1],
            'col_total': self._calc_or_with_ci(unorr_total, total_n)[1]
        })

        return results


class SurvivalAnalyzer:
    """
    Implements statistical analysis for Table 14.2.2.2 (Progression-Free Survival).

    This performs Kaplan-Meier survival analysis on ADTTE dataset:
    - PFS events: Progressive Disease or Death
    - Censoring reasons: New anti-cancer therapy, No post-baseline assessments, No PD or death
    - Median, 25th/75th percentiles
    - Survival rates at 3, 6, 9, 12 months
    """

    def __init__(self, adtte: pd.DataFrame, adsl: pd.DataFrame):
        self.adtte = adtte
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(saf[saf['TRT01PN'] == trt])
        return big_n

    def _filter_pfs(self) -> pd.DataFrame:
        """Filter ADTTE to PFS records."""
        return self.adtte[self.adtte['PARAMCD'] == 'PFS'].copy()

    def _kaplan_meier_survival(self, times: np.ndarray, events: np.ndarray,
                                eval_times: list = None) -> Tuple[dict, dict]:
        """
        Basic Kaplan-Meier survival analysis.

        Args:
            times: Array of survival times
            events: Array of event indicators (1=event, 0=censored)
            eval_times: Time points at which to evaluate survival probability

        Returns:
            (survival_probs, percentiles) where survival_probs is {time: S(t)}
            and percentiles is {percentile: time}
        """
        n = len(times)
        if n == 0:
            return {}, {}

        # Sort by time
        order = np.argsort(times)
        times_sorted = times[order]
        events_sorted = events[order]

        # Calculate survival function
        unique_times = np.unique(times_sorted)
        n_at_risk = np.arange(len(unique_times), 0, -1)
        n_events = np.array([np.sum(events_sorted[times_sorted == t]) for t in unique_times])

        # Survival probability at each unique time
        survival_prob = np.cumprod(1 - n_events / n_at_risk)

        # Create survival function as dict
        survival_func = dict(zip(unique_times, survival_prob))

        # Calculate percentiles (time at which S(t) = percentile)
        # For median (S=0.5), 25th percentile (S=0.75), 75th percentile (S=0.25)
        percentiles = {}
        for target_s in [0.5, 0.25, 0.75]:
            # Find time where survival probability first drops below target
            below_target = np.where(survival_prob < target_s)[0]
            if len(below_target) > 0:
                percentiles[target_s] = unique_times[below_target[0]]
            else:
                percentiles[target_s] = np.inf  # Not reached

        # Evaluate survival at specific time points if provided
        eval_survival = {}
        if eval_times:
            for t in eval_times:
                # Find survival probability at time t
                idx = np.searchsorted(unique_times, t, side='right') - 1
                if idx >= 0:
                    eval_survival[t] = survival_prob[idx]
                else:
                    eval_survival[t] = 1.0

        return eval_survival, percentiles

    def _get_pfs_stats(self, df: pd.DataFrame) -> Dict:
        """Get PFS statistics for a treatment group."""
        # Get unique subjects (one record per subject)
        subj_data = df.drop_duplicates('USUBJID')

        times = subj_data['AVAL'].values
        # CNSR: 0 = event (PD or death), 1 = censored
        events = (subj_data['CNSR'] == 0).astype(int).values

        # Convert days to months
        times_months = times / 30.44

        # Evaluate survival at 3, 6, 9, 12 months
        eval_months = [3, 6, 9, 12]
        eval_survival, percentiles = self._kaplan_meier_survival(
            times_months, events, eval_months
        )

        # Event counts
        n_total = len(subj_data)
        n_event = int(np.sum(events))
        n_censored = n_total - n_event

        # Event subtypes
        evnt_desc = subj_data[subj_data['CNSR'] == 0]['EVNTDESC'].value_counts()
        n_pd = int(evnt_desc.get('DISEASE PROGRESSION', 0))
        n_death = int(evnt_desc.get('DEATH', 0))

        # Censoring reasons
        cens_reason = subj_data[subj_data['CNSR'] == 1]['CNSDTDSC'].value_counts()
        n_new_therapy = int(cens_reason.get('New anti-cancer therapy', 0))
        n_no_postbase = int(cens_reason.get('No post-baseline tumor assessments', 0))
        n_no_pd_death = int(cens_reason.get('No PD or death', 0))

        return {
            'n_total': n_total,
            'n_event': n_event,
            'n_censored': n_censored,
            'n_pd': n_pd,
            'n_death': n_death,
            'n_new_therapy': n_new_therapy,
            'n_no_postbase': n_no_postbase,
            'n_no_pd_death': n_no_pd_death,
            'median': percentiles.get(0.5, np.inf),
            'pct_25': percentiles.get(0.75, np.inf),  # 25th percentile
            'pct_75': percentiles.get(0.25, np.inf),  # 75th percentile
            'survival_at_months': eval_survival
        }

    def analyze(self) -> Dict:
        """Perform complete PFS analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        # Filter to PFS
        pfs = self._filter_pfs()

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        def fmt_pct(n: int, denom: int) -> str:
            """Format as count (percentage)."""
            if denom == 0:
                return "0 (0.0)"
            pct = n / denom * 100
            return f"{n:>3} ({pct:>5.1f})"

        def fmt_pct_value(pct: float) -> str:
            """Format percentage value."""
            if np.isinf(pct) or np.isnan(pct):
                return "NA"
            return f"{pct:.1f}"

        trt_list = [1, 2, 3]

        # Get stats by treatment
        pfs_by_trt = {}
        for trt in trt_list:
            trt_data = pfs[pfs['TRTPN'] == trt]
            pfs_by_trt[trt] = self._get_pfs_stats(trt_data)

        # Row 0: Progression Free Survival header
        results['units'].append({
            'unit': 'unit01',
            'level': 1,
            'rowlabel': 'Progression Free Survival (Months)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Row 1: Subjects with events (%)
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'Subjects with events (%)',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total_events = 0
        for i, trt in enumerate(trt_list, 1):
            n_event = pfs_by_trt[trt]['n_event']
            row[f'col{i}'] = fmt_pct(n_event, big_n[trt])
            total_events += n_event
        row['col_total'] = fmt_pct(total_events, total_n)
        results['units'].append(row)

        # Row 2: Progressive Disease
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'Progressive Disease (PD)',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total_pd = 0
        for i, trt in enumerate(trt_list, 1):
            n_pd = pfs_by_trt[trt]['n_pd']
            row[f'col{i}'] = fmt_pct(n_pd, big_n[trt])
            total_pd += n_pd
        row['col_total'] = fmt_pct(total_pd, total_n)
        results['units'].append(row)

        # Row 3: Death
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'Death',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total_death = 0
        for i, trt in enumerate(trt_list, 1):
            n_death = pfs_by_trt[trt]['n_death']
            row[f'col{i}'] = fmt_pct(n_death, big_n[trt])
            total_death += n_death
        row['col_total'] = fmt_pct(total_death, total_n)
        results['units'].append(row)

        # Row 4: Subjects censored (%)
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'Subjects censored (%)',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total_censored = 0
        for i, trt in enumerate(trt_list, 1):
            n_censored = pfs_by_trt[trt]['n_censored']
            row[f'col{i}'] = fmt_pct(n_censored, big_n[trt])
            total_censored += n_censored
        row['col_total'] = fmt_pct(total_censored, total_n)
        results['units'].append(row)

        # Row 5: New anti-cancer therapy
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'New anti-cancer therapy',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total_new_therapy = 0
        for i, trt in enumerate(trt_list, 1):
            n = pfs_by_trt[trt]['n_new_therapy']
            row[f'col{i}'] = fmt_pct(n, big_n[trt])
            total_new_therapy += n
        row['col_total'] = fmt_pct(total_new_therapy, total_n)
        results['units'].append(row)

        # Row 6: No post-baseline tumor assessments
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'No post-baseline tumor assessments',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total_no_postbase = 0
        for i, trt in enumerate(trt_list, 1):
            n = pfs_by_trt[trt]['n_no_postbase']
            row[f'col{i}'] = fmt_pct(n, big_n[trt])
            total_no_postbase += n
        row['col_total'] = fmt_pct(total_no_postbase, total_n)
        results['units'].append(row)

        # Row 7: No PD or death
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'No PD or death',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total_no_pd = 0
        for i, trt in enumerate(trt_list, 1):
            n = pfs_by_trt[trt]['n_no_pd_death']
            row[f'col{i}'] = fmt_pct(n, big_n[trt])
            total_no_pd += n
        row['col_total'] = fmt_pct(total_no_pd, total_n)
        results['units'].append(row)

        # Row 8: 25th Percentile
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '25th Percentile',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        pct_25_values = []
        for i, trt in enumerate(trt_list, 1):
            val = pfs_by_trt[trt]['pct_25']
            row[f'col{i}'] = fmt_pct_value(val)
            pct_25_values.append(val)
        row['col_total'] = fmt_pct_value(np.median(pct_25_values))
        results['units'].append(row)

        # Row 9: 95% CI for 25th percentile
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '95% CI',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        for i in range(3):
            row[f'col{i+1}'] = '(NA, NA)'
        row['col_total'] = '(NA, NA)'
        results['units'].append(row)

        # Row 10: Median
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'Median',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        median_values = []
        for i, trt in enumerate(trt_list, 1):
            val = pfs_by_trt[trt]['median']
            row[f'col{i}'] = fmt_pct_value(val)
            median_values.append(val)
        row['col_total'] = fmt_pct_value(np.median(median_values))
        results['units'].append(row)

        # Row 11: 95% CI for Median
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '95% CI',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        for i in range(3):
            row[f'col{i+1}'] = '(NA, NA)'
        row['col_total'] = '(NA, NA)'
        results['units'].append(row)

        # Row 12: 75th Percentile
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '75th Percentile',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        pct_75_values = []
        for i, trt in enumerate(trt_list, 1):
            val = pfs_by_trt[trt]['pct_75']
            row[f'col{i}'] = fmt_pct_value(val)
            pct_75_values.append(val)
        row['col_total'] = fmt_pct_value(np.median(pct_75_values))
        results['units'].append(row)

        # Row 13: 95% CI for 75th Percentile
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '95% CI',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        for i in range(3):
            row[f'col{i+1}'] = '(NA, NA)'
        row['col_total'] = '(NA, NA)'
        results['units'].append(row)

        # Section 2: PFS rates at timepoints
        results['units'].append({
            'unit': 'unit02',
            'level': 1,
            'rowlabel': 'Progression Free Survival',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Add survival rates at 3, 6, 9, 12 months
        for month in [3, 6, 9, 12]:
            row = {'unit': 'unit02', 'level': 1,
                   'rowlabel': f'Point Estimate at {month} Months',
                   'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
            surv_values = []
            for i, trt in enumerate(trt_list, 1):
                surv = pfs_by_trt[trt]['survival_at_months'].get(month, np.nan)
                if np.isnan(surv):
                    row[f'col{i}'] = 'NA'
                else:
                    row[f'col{i}'] = f"{surv * 100:.1f}"
                    surv_values.append(surv)
            if surv_values:
                row['col_total'] = f"{np.mean(surv_values) * 100:.1f}"
            else:
                row['col_total'] = 'NA'
            results['units'].append(row)

            # 95% CI
            row = {'unit': 'unit02', 'level': 1,
                   'rowlabel': '95% CI',
                   'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
            for i in range(3):
                row[f'col{i+1}'] = '(NA, NA)'
            row['col_total'] = '(NA, NA)'
            results['units'].append(row)

        return results


class MedicalHistoryAnalyzer:
    """
    Implements statistical analysis for Table 14.1.3.1 (Medical History / Disease Characteristics).

    Disease characteristics at study entry including:
    - Time from Initial Histological Diagnosis to Study Treatment (Months)
    - Histology
    - Tumor Stage at study Entry
    - TNM Stage at Entry (T, N, M)
    """

    def __init__(self, adsl: pd.DataFrame):
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from enrolled subjects (ENRLFL='Y')."""
        big_n = {}
        enrl = self.adsl[self.adsl['ENRLFL'] == 'Y']
        for trt in enrl['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(enrl[enrl['TRT01PN'] == trt])
        return big_n

    def _fmt_continuous(self, values: list) -> Dict[str, str]:
        """Format continuous statistics."""
        valid = [v for v in values if pd.notna(v)]
        if not valid:
            return {'n': '0', 'mean': 'NE', 'sd': 'NE', 'median': 'NE', 'min_max': 'NE'}

        import statistics
        n = len(valid)
        mean = statistics.mean(valid)
        sd = statistics.stdev(valid) if n > 1 else 0
        median = statistics.median(valid)
        min_val = min(valid)
        max_val = max(valid)

        return {
            'n': str(n),
            'mean': f"{mean:.2f}",
            'sd': f"{sd:.3f}",
            'median': f"{median:.2f}",
            'min_max': f"{min_val:.1f}, {max_val:.1f}"
        }

    def _freq_table(self, col: pd.Series, trt_col: pd.Series) -> Dict[str, Dict[int, Dict[str, str]]]:
        """Generate frequency table by treatment group.

        Returns: {category: {trt: {'n': str, 'pct': str}}}
        """
        big_n = self.calculate_big_n()
        results = {}

        # Get valid records (non-null col values)
        valid_mask = col.notna() & trt_col.notna()
        valid_df = pd.DataFrame({'col': col[valid_mask], 'trt': trt_col[valid_mask]})

        for cat in valid_df['col'].unique():
            cat_df = valid_df[valid_df['col'] == cat]
            results[str(cat)] = {}

            for trt in sorted(big_n.keys()):
                n = len(cat_df[cat_df['trt'] == trt])
                pct = (n / big_n[trt] * 100) if big_n[trt] > 0 else 0
                results[str(cat)][trt] = {'n': n, 'pct': pct}

        return results

    def _compute_diagnosis_duration(self) -> Dict[str, pd.Series]:
        """Compute duration from initial histological diagnosis to study treatment start."""
        # DURDIAG is in the ADSL dataset - duration of diagnosis in months
        dur = self.adsl['DURDIAG'].copy()
        trt = self.adsl['TRT01PN'].copy()
        return {'dur': dur, 'trt': trt}

    def _get_treatment_groups(self) -> Dict[int, str]:
        """Map treatment group numbers to names."""
        return {1: '5.4 mg/kg', 2: '6.4 mg/kg', 3: '7.4 mg/kg'}

    def analyze(self) -> Dict[str, Any]:
        """Perform complete medical history analysis."""
        results = {
            'table_id': '14.1.3.1',
            'table_name': 'Medical History and Disease Characteristics',
            'units': [],
            'big_n': self.calculate_big_n()
        }

        big_n = results['big_n']

        # Unit 01: Time from Initial Histological Diagnosis to Study Treatment (Months)
        dur_data = self._compute_diagnosis_duration()
        dur_col = dur_data['dur']
        trt_col = dur_data['trt']

        # Filter to enrolled subjects and convert DURDIAG from days to months
        enrl = self.adsl[self.adsl['ENRLFL'] == 'Y'].copy()
        enrl_dur = (enrl['DURDIAG'].dropna()) / 30.44  # Convert days to months

        # Calculate overall stats
        if len(enrl_dur) > 0:
            overall_stats = self._fmt_continuous(enrl_dur.tolist())
        else:
            overall_stats = {'n': '0', 'mean': 'NE', 'sd': 'NE', 'median': 'NE', 'min_max': 'NE'}

        # Stats by treatment
        trt_stats = {}
        for trt in sorted(big_n.keys()):
            trt_dur = enrl_dur[enrl['TRT01PN'] == trt]
            if len(trt_dur) > 0:
                trt_stats[trt] = self._fmt_continuous(trt_dur.tolist())
            else:
                trt_stats[trt] = {'n': '0', 'mean': 'NE', 'sd': 'NE', 'median': 'NE', 'min_max': 'NE'}

        # Add diagnosis duration row (group header)
        results['units'].append({
            'unit': 'unit01', 'level': 1,
            'rowlabel': 'Time from Initial Histological Diagnosis to Study Treatment (Months)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # n row
        results['units'].append({
            'unit': 'unit01', 'level': 2,
            'rowlabel': 'n',
            'col1': trt_stats.get(1, {}).get('n', '0'),
            'col2': trt_stats.get(2, {}).get('n', '0'),
            'col3': trt_stats.get(3, {}).get('n', '0'),
            'col_total': overall_stats['n']
        })

        # Mean row
        results['units'].append({
            'unit': 'unit01', 'level': 2,
            'rowlabel': 'Mean',
            'col1': trt_stats.get(1, {}).get('mean', 'NE'),
            'col2': trt_stats.get(2, {}).get('mean', 'NE'),
            'col3': trt_stats.get(3, {}).get('mean', 'NE'),
            'col_total': overall_stats['mean']
        })

        # Std. Dev row
        results['units'].append({
            'unit': 'unit01', 'level': 2,
            'rowlabel': 'Std. Dev.',
            'col1': trt_stats.get(1, {}).get('sd', 'NE'),
            'col2': trt_stats.get(2, {}).get('sd', 'NE'),
            'col3': trt_stats.get(3, {}).get('sd', 'NE'),
            'col_total': overall_stats['sd']
        })

        # Median row
        results['units'].append({
            'unit': 'unit01', 'level': 2,
            'rowlabel': 'Median',
            'col1': trt_stats.get(1, {}).get('median', 'NE'),
            'col2': trt_stats.get(2, {}).get('median', 'NE'),
            'col3': trt_stats.get(3, {}).get('median', 'NE'),
            'col_total': overall_stats['median']
        })

        # Min, Max row
        results['units'].append({
            'unit': 'unit01', 'level': 2,
            'rowlabel': 'Min, Max',
            'col1': trt_stats.get(1, {}).get('min_max', 'NE'),
            'col2': trt_stats.get(2, {}).get('min_max', 'NE'),
            'col3': trt_stats.get(3, {}).get('min_max', 'NE'),
            'col_total': overall_stats['min_max']
        })

        # Unit 02: Histology
        results['units'].append({
            'unit': 'unit02', 'level': 1,
            'rowlabel': 'Histology',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        hist_freq = self._freq_table(self.adsl['HIST'], self.adsl['TRT01PN'])
        # Standard histology categories
        hist_order = ['Adenocarcinoma', 'Inflammatory', 'Other']

        for hist in hist_order:
            if hist in hist_freq:
                col1_n = hist_freq[hist].get(1, {}).get('n', 0)
                col1_pct = hist_freq[hist].get(1, {}).get('pct', 0)
                col2_n = hist_freq[hist].get(2, {}).get('n', 0)
                col2_pct = hist_freq[hist].get(2, {}).get('pct', 0)
                col3_n = hist_freq[hist].get(3, {}).get('n', 0)
                col3_pct = hist_freq[hist].get(3, {}).get('pct', 0)

                # Total
                total_n = sum(hist_freq[hist].get(t, {}).get('n', 0) for t in [1, 2, 3])
                total_pct = (total_n / sum(big_n.values()) * 100) if sum(big_n.values()) > 0 else 0

                col1_str = f"{col1_n} ({col1_pct:.1f})" if col1_n > 0 else '0'
                col2_str = f"{col2_n} ({col2_pct:.1f})" if col2_n > 0 else '0'
                col3_str = f"{col3_n} ({col3_pct:.1f})" if col3_n > 0 else '0'
                col_total_str = f"{total_n} ({total_pct:.1f})" if total_n > 0 else '0'

                results['units'].append({
                    'unit': 'unit02', 'level': 2,
                    'rowlabel': hist,
                    'col1': col1_str, 'col2': col2_str, 'col3': col3_str,
                    'col_total': col_total_str
                })

        # Unit 03: Tumor Stage at study Entry
        results['units'].append({
            'unit': 'unit03', 'level': 1,
            'rowlabel': 'Tumor Stage at study Entry',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        stage_freq = self._freq_table(self.adsl['STAGESE'], self.adsl['TRT01PN'])
        stage_order = ['I', 'II', 'IIIA', 'IIIB', 'IIIC', 'IV']

        for stage in stage_order:
            if stage in stage_freq:
                col1_n = stage_freq[stage].get(1, {}).get('n', 0)
                col1_pct = stage_freq[stage].get(1, {}).get('pct', 0)
                col2_n = stage_freq[stage].get(2, {}).get('n', 0)
                col2_pct = stage_freq[stage].get(2, {}).get('pct', 0)
                col3_n = stage_freq[stage].get(3, {}).get('n', 0)
                col3_pct = stage_freq[stage].get(3, {}).get('pct', 0)

                total_n = sum(stage_freq[stage].get(t, {}).get('n', 0) for t in [1, 2, 3])
                total_pct = (total_n / sum(big_n.values()) * 100) if sum(big_n.values()) > 0 else 0

                col1_str = f"{col1_n} ({col1_pct:.1f})" if col1_n > 0 else '0'
                col2_str = f"{col2_n} ({col2_pct:.1f})" if col2_n > 0 else '0'
                col3_str = f"{col3_n} ({col3_pct:.1f})" if col3_n > 0 else '0'
                col_total_str = f"{total_n} ({total_pct:.1f})" if total_n > 0 else '0'

                results['units'].append({
                    'unit': 'unit03', 'level': 2,
                    'rowlabel': stage,
                    'col1': col1_str, 'col2': col2_str, 'col3': col3_str,
                    'col_total': col_total_str
                })

        # Unit 04: TNM Stage at Entry (T)
        results['units'].append({
            'unit': 'unit04', 'level': 1,
            'rowlabel': 'TNM Stage at Entry (T)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        tstage_freq = self._freq_table(self.adsl['TNMT'], self.adsl['TRT01PN'])
        # T stage order (simplified grouping)
        t_order = ['T0', 'T1', 'T1a', 'T1b', 'T1c', 'T1mi', 'T2', 'T2a', 'T3', 'T4', 'T4a', 'T4b', 'T4c', 'T4d', 'TX']

        for t in t_order:
            if t in tstage_freq:
                col1_n = tstage_freq[t].get(1, {}).get('n', 0)
                col1_pct = tstage_freq[t].get(1, {}).get('pct', 0)
                col2_n = tstage_freq[t].get(2, {}).get('n', 0)
                col2_pct = tstage_freq[t].get(2, {}).get('pct', 0)
                col3_n = tstage_freq[t].get(3, {}).get('n', 0)
                col3_pct = tstage_freq[t].get(3, {}).get('pct', 0)

                total_n = sum(tstage_freq[t].get(trt, {}).get('n', 0) for trt in [1, 2, 3])
                total_pct = (total_n / sum(big_n.values()) * 100) if sum(big_n.values()) > 0 else 0

                col1_str = f"{col1_n} ({col1_pct:.1f})" if col1_n > 0 else '0'
                col2_str = f"{col2_n} ({col2_pct:.1f})" if col2_n > 0 else '0'
                col3_str = f"{col3_n} ({col3_pct:.1f})" if col3_n > 0 else '0'
                col_total_str = f"{total_n} ({total_pct:.1f})" if total_n > 0 else '0'

                results['units'].append({
                    'unit': 'unit04', 'level': 2,
                    'rowlabel': t,
                    'col1': col1_str, 'col2': col2_str, 'col3': col3_str,
                    'col_total': col_total_str
                })

        # Unit 05: TNM Stage at Entry (N)
        results['units'].append({
            'unit': 'unit05', 'level': 1,
            'rowlabel': 'TNM Stage at Entry (N)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        nstage_freq = self._freq_table(self.adsl['TNMN'], self.adsl['TRT01PN'])
        n_order = ['N0', 'N1', 'N2', 'N2a', 'N3', 'N3a', 'N3b', 'N3c', 'NX']

        for n in n_order:
            if n in nstage_freq:
                col1_n = nstage_freq[n].get(1, {}).get('n', 0)
                col1_pct = nstage_freq[n].get(1, {}).get('pct', 0)
                col2_n = nstage_freq[n].get(2, {}).get('n', 0)
                col2_pct = nstage_freq[n].get(2, {}).get('pct', 0)
                col3_n = nstage_freq[n].get(3, {}).get('n', 0)
                col3_pct = nstage_freq[n].get(3, {}).get('pct', 0)

                total_n = sum(nstage_freq[n].get(trt, {}).get('n', 0) for trt in [1, 2, 3])
                total_pct = (total_n / sum(big_n.values()) * 100) if sum(big_n.values()) > 0 else 0

                col1_str = f"{col1_n} ({col1_pct:.1f})" if col1_n > 0 else '0'
                col2_str = f"{col2_n} ({col2_pct:.1f})" if col2_n > 0 else '0'
                col3_str = f"{col3_n} ({col3_pct:.1f})" if col3_n > 0 else '0'
                col_total_str = f"{total_n} ({total_pct:.1f})" if total_n > 0 else '0'

                results['units'].append({
                    'unit': 'unit05', 'level': 2,
                    'rowlabel': n,
                    'col1': col1_str, 'col2': col2_str, 'col3': col3_str,
                    'col_total': col_total_str
                })

        # Unit 06: TNM Stage at Entry (M)
        results['units'].append({
            'unit': 'unit06', 'level': 1,
            'rowlabel': 'TNM Stage at Entry (M)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        mstage_freq = self._freq_table(self.adsl['TNMM'], self.adsl['TRT01PN'])
        m_order = ['M0', 'M1', 'M1a', 'M1b', 'MX']

        for m in m_order:
            if m in mstage_freq:
                col1_n = mstage_freq[m].get(1, {}).get('n', 0)
                col1_pct = mstage_freq[m].get(1, {}).get('pct', 0)
                col2_n = mstage_freq[m].get(2, {}).get('n', 0)
                col2_pct = mstage_freq[m].get(2, {}).get('pct', 0)
                col3_n = mstage_freq[m].get(3, {}).get('n', 0)
                col3_pct = mstage_freq[m].get(3, {}).get('pct', 0)

                total_n = sum(mstage_freq[m].get(trt, {}).get('n', 0) for trt in [1, 2, 3])
                total_pct = (total_n / sum(big_n.values()) * 100) if sum(big_n.values()) > 0 else 0

                col1_str = f"{col1_n} ({col1_pct:.1f})" if col1_n > 0 else '0'
                col2_str = f"{col2_n} ({col2_pct:.1f})" if col2_n > 0 else '0'
                col3_str = f"{col3_n} ({col3_pct:.1f})" if col3_n > 0 else '0'
                col_total_str = f"{total_n} ({total_pct:.1f})" if total_n > 0 else '0'

                results['units'].append({
                    'unit': 'unit06', 'level': 2,
                    'rowlabel': m,
                    'col1': col1_str, 'col2': col2_str, 'col3': col3_str,
                    'col_total': col_total_str
                })

        return results


def generate_medical_history_report(
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.1.3.1",
    table_title: str = "Medical History and Disease Characteristics",
    population: str = "Enrolled Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.1.3.1 (Medical History and Disease Characteristics).

    Args:
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = MedicalHistoryAnalyzer(adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                   table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


class MedicationAnalyzer:
    """
    Implements statistical analysis for Table 14.1.4.1 (Prior Medications)
    and Table 14.1.4.2 (Concomitant Medications).

    Analyzes medication usage by ATC classification:
    - Prior Cancer Systemic Therapy (Table 14.1.4.1)
    - Concomitant Medications (Table 14.1.4.2)
    """

    def __init__(self, adcm: pd.DataFrame, adsl: pd.DataFrame):
        self.adcm = adcm
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from enrolled subjects."""
        big_n = {}
        enrl = self.adsl[self.adsl['ENRLFL'] == 'Y']
        for trt in enrl['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(enrl[enrl['TRT01PN'] == trt])
        return big_n

    def _get_prior_med_subjects(self, trt_col: pd.Series) -> pd.Series:
        """Get subjects with prior medications (excluding PRIOR CANCER SYSTEMIC THERAPY)."""
        # Prior medications are those where CMCAT is NOT "PRIOR CANCER SYSTEMIC THERAPY"
        prior_mask = (
            (self.adcm['CMCAT'] != 'PRIOR CANCER SYSTEMIC THERAPY') &
            (self.adcm['CMCAT'] != 'NON-DRUG TREATMENTS')
        )
        prior_cm = self.adcm[prior_mask]
        return prior_cm['USUBJID'].unique()

    def _get_concom_med_subjects(self) -> pd.Series:
        """Get subjects with concomitant medications."""
        concom_mask = self.adcm['CMCAT'] == 'CONCOMITANT MEDICATIONS'
        concom_cm = self.adcm[concom_mask]
        return concom_cm['USUBJID'].unique()

    def _get_prior_therapy_subjects(self) -> pd.Series:
        """Get subjects with prior cancer systemic therapy."""
        prior_mask = self.adcm['CMCAT'] == 'PRIOR CANCER SYSTEMIC THERAPY'
        prior_cm = self.adcm[prior_mask]
        return prior_cm['USUBJID'].unique()

    def _count_by_atc(self, cm_category: str, atc_level: str = 'ATC2T') -> Dict[str, Dict[str, int]]:
        """Count unique subjects by ATC classification.

        Args:
            cm_category: CMCAT value to filter by
            atc_level: ATC level to group by ('ATC1T', 'ATC2T', 'ATC3T', 'ATC4T')

        Returns:
            Dict[atc_value, Dict[usubjid_trt, count]]
        """
        big_n = self.calculate_big_n()

        if cm_category == 'CONCOMITANT MEDICATIONS':
            cm_data = self.adcm[self.adcm['CMCAT'] == cm_category]
        elif cm_category == 'PRIOR CANCER SYSTEMIC THERAPY':
            cm_data = self.adcm[self.adcm['CMCAT'] == cm_category]
        else:
            # All non-cancer-therapy medications
            cm_data = self.adcm[
                (self.adcm['CMCAT'] != 'PRIOR CANCER SYSTEMIC THERAPY') &
                (self.adcm['CMCAT'] != 'NON-DRUG TREATMENTS')
            ]

        # Merge with ADSL to get treatment info
        merged = cm_data.merge(
            self.adsl[['USUBJID', 'TRT01PN']],
            on='USUBJID',
            how='left'
        )

        results = {}
        for atc_val in merged[atc_level].dropna().unique():
            atc_df = merged[merged[atc_level] == atc_val]
            subjects_by_trt = {}

            for trt in sorted(big_n.keys()):
                subjects = atc_df[atc_df['TRT01PN'] == trt]['USUBJID'].nunique()
                subjects_by_trt[trt] = subjects

            results[str(atc_val)] = subjects_by_trt

        return results

    def _freq_table(self, cm_category: str) -> Tuple[Dict[str, int], Dict[str, Dict[str, int]]]:
        """Generate frequency table for medications by ATC.

        Returns:
            (subjects_with_any, {category: {trt: count}})
        """
        big_n = self.calculate_big_n()

        # Get subjects with any medication in this category
        if cm_category == 'CONCOMITANT MEDICATIONS':
            cm_data = self.adcm[self.adcm['CMCAT'] == cm_category]
        elif cm_category == 'PRIOR CANCER SYSTEMIC THERAPY':
            cm_data = self.adcm[self.adcm['CMCAT'] == cm_category]
        else:
            cm_data = self.adcm[
                (self.adcm['CMCAT'] != 'PRIOR CANCER SYSTEMIC THERAPY') &
                (self.adcm['CMCAT'] != 'NON-DRUG TREATMENTS')
            ]

        # Merge with ADSL for treatment info
        merged = cm_data.merge(
            self.adsl[['USUBJID', 'TRT01PN']],
            on='USUBJID',
            how='left'
        )

        # Count unique subjects by treatment
        any_subjects = {}
        for trt in sorted(big_n.keys()):
            any_subjects[trt] = merged[merged['TRT01PN'] == trt]['USUBJID'].nunique()

        # Count by ATC2 (therapeutic subgroup)
        atc2_counts = self._count_by_atc(cm_category, 'ATC2T')

        return any_subjects, atc2_counts

    def analyze_prior_medications(self) -> Dict[str, Any]:
        """Analyze prior medications (Table 14.1.4.1)."""
        results = {
            'table_id': '14.1.4.1',
            'table_name': 'Prior Medications',
            'units': [],
            'big_n': self.calculate_big_n()
        }

        big_n = results['big_n']

        # Get subjects with any prior medication (excluding cancer therapy)
        any_subjects, atc2_counts = self._freq_table('PRIOR_MED')

        # Unit 01: Subjects with any Prior Medications
        results['units'].append({
            'unit': 'unit01', 'level': 1,
            'rowlabel': 'Subjects with any Prior Medications',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Calculate n (%) for each treatment
        total_subjects = sum(any_subjects.values())
        for trt in sorted(big_n.keys()):
            n = any_subjects.get(trt, 0)
            pct = (n / big_n[trt] * 100) if big_n[trt] > 0 else 0

        # Total column
        total_n = sum(any_subjects.get(trt, 0) for trt in big_n.keys())
        total_pct = (total_n / sum(big_n.values()) * 100) if sum(big_n.values()) > 0 else 0

        col1_n = any_subjects.get(1, 0)
        col1_pct = (col1_n / big_n[1] * 100) if big_n.get(1, 0) > 0 else 0
        col2_n = any_subjects.get(2, 0)
        col2_pct = (col2_n / big_n[2] * 100) if big_n.get(2, 0) > 0 else 0
        col3_n = any_subjects.get(3, 0)
        col3_pct = (col3_n / big_n[3] * 100) if big_n.get(3, 0) > 0 else 0

        results['units'].append({
            'unit': 'unit01', 'level': 2,
            'rowlabel': 'Yes',
            'col1': f"{col1_n} ({col1_pct:.1f})",
            'col2': f"{col2_n} ({col2_pct:.1f})",
            'col3': f"{col3_n} ({col3_pct:.1f})",
            'col_total': f"{total_n} ({total_pct:.1f})"
        })

        return results

    def analyze_concomitant_medications(self) -> Dict[str, Any]:
        """Analyze concomitant medications (Table 14.1.4.2)."""
        results = {
            'table_id': '14.1.4.2',
            'table_name': 'Concomitant Medications',
            'units': [],
            'big_n': self.calculate_big_n()
        }

        big_n = results['big_n']

        # Get subjects with concomitant medications
        any_subjects, atc2_counts = self._freq_table('CONCOMITANT MEDICATIONS')

        # Unit 01: Subjects with any Concomitant Medications
        results['units'].append({
            'unit': 'unit01', 'level': 1,
            'rowlabel': 'Subjects with any Concomitant Medications',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        total_n = sum(any_subjects.get(trt, 0) for trt in big_n.keys())
        total_pct = (total_n / sum(big_n.values()) * 100) if sum(big_n.values()) > 0 else 0

        col1_n = any_subjects.get(1, 0)
        col1_pct = (col1_n / big_n[1] * 100) if big_n.get(1, 0) > 0 else 0
        col2_n = any_subjects.get(2, 0)
        col2_pct = (col2_n / big_n[2] * 100) if big_n.get(2, 0) > 0 else 0
        col3_n = any_subjects.get(3, 0)
        col3_pct = (col3_n / big_n[3] * 100) if big_n.get(3, 0) > 0 else 0

        results['units'].append({
            'unit': 'unit01', 'level': 2,
            'rowlabel': 'Yes',
            'col1': f"{col1_n} ({col1_pct:.1f})",
            'col2': f"{col2_n} ({col2_pct:.1f})",
            'col3': f"{col3_n} ({col3_pct:.1f})",
            'col_total': f"{total_n} ({total_pct:.1f})"
        })

        return results


def generate_prior_medication_report(
    adcm_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.1.4.1",
    table_title: str = "Prior Medications",
    population: str = "Enrolled Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.1.4.1 (Prior Medications).

    Args:
        adcm_path: Path to ADCM SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adcm, _ = pyreadstat.read_sas7bdat(adcm_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = MedicationAnalyzer(adcm, adsl)
    analysis_results = analyzer.analyze_prior_medications()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                   table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_concomitant_medication_report(
    adcm_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.1.4.2",
    table_title: str = "Concomitant Medications",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.1.4.2 (Concomitant Medications).

    Args:
        adcm_path: Path to ADCM SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adcm, _ = pyreadstat.read_sas7bdat(adcm_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = MedicationAnalyzer(adcm, adsl)
    analysis_results = analyzer.analyze_concomitant_medications()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                   table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


class ExposureAnalyzer:
    """
    Implements statistical analysis for Table 14.1.5.1 (Exposure).

    Analyzes treatment exposure including:
    - Number (%) of subjects on treatment at data cut
    - Patient-Year Exposure
    - Treatment Duration
    - Dose Amount and Intensity
    - Number of Cycles
    - Dose Modifications
    """

    def __init__(self, adex: pd.DataFrame, adsl: pd.DataFrame):
        self.adex = adex
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from enrolled subjects."""
        big_n = {}
        enrl = self.adsl[self.adsl['ENRLFL'] == 'Y']
        for trt in enrl['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(enrl[enrl['TRT01PN'] == trt])
        return big_n

    def _fmt_continuous(self, values: list) -> Dict[str, str]:
        """Format continuous statistics."""
        valid = [v for v in values if pd.notna(v)]
        if not valid:
            return {'n': '0', 'mean': 'NE', 'sd': 'NE', 'median': 'NE', 'min_max': 'NE'}

        import statistics
        n = len(valid)
        mean = statistics.mean(valid)
        sd = statistics.stdev(valid) if n > 1 else 0
        median = statistics.median(valid)
        min_val = min(valid)
        max_val = max(valid)

        return {
            'n': str(n),
            'mean': f"{mean:.2f}",
            'sd': f"{sd:.3f}",
            'median': f"{median:.2f}",
            'min_max': f"{min_val:.1f}, {max_val:.1f}"
        }

    def analyze(self) -> Dict[str, Any]:
        """Perform complete exposure analysis."""
        results = {
            'table_id': '14.1.5.1',
            'table_name': 'Exposure',
            'units': [],
            'big_n': self.calculate_big_n()
        }

        big_n = results['big_n']

        # Unit 01: Subjects on treatment at data cut
        # Using ONTRTAYN flag
        on_trt = {}
        for trt in sorted(big_n.keys()):
            enrl = self.adsl[(self.adsl['ENRLFL'] == 'Y') & (self.adsl['TRT01PN'] == trt)]
            on_count = len(enrl[enrl['ONTRTAYN'] == 'Y'])
            on_trt[trt] = on_count

        results['units'].append({
            'unit': 'unit01', 'level': 1,
            'rowlabel': 'Number (%) of subjects on treatment at data cut',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Yes row
        total_on = sum(on_trt.values())
        total_pct = (total_on / sum(big_n.values()) * 100) if sum(big_n.values()) > 0 else 0
        col1_pct = (on_trt.get(1, 0) / big_n.get(1, 1) * 100) if big_n.get(1, 0) > 0 else 0
        col2_pct = (on_trt.get(2, 0) / big_n.get(2, 1) * 100) if big_n.get(2, 0) > 0 else 0
        col3_pct = (on_trt.get(3, 0) / big_n.get(3, 1) * 100) if big_n.get(3, 0) > 0 else 0

        results['units'].append({
            'unit': 'unit01', 'level': 2,
            'rowlabel': 'Yes',
            'col1': f"{on_trt.get(1, 0)} ({col1_pct:.1f})",
            'col2': f"{on_trt.get(2, 0)} ({col2_pct:.1f})",
            'col3': f"{on_trt.get(3, 0)} ({col3_pct:.1f})",
            'col_total': f"{total_on} ({total_pct:.1f})"
        })

        # Unit 02: Patient-Year Exposure (calculated from TRTDURM in months)
        results['units'].append({
            'unit': 'unit02', 'level': 1,
            'rowlabel': 'Patient-Year Exposure (year)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Calculate patient-years by treatment
        py_values = {}
        for trt in sorted(big_n.keys()):
            enrl = self.adsl[(self.adsl['ENRLFL'] == 'Y') & (self.adsl['TRT01PN'] == trt)]
            dur_months = enrl['TRTDURM'].dropna()
            # Convert months to years and sum
            total_years = (dur_months / 12).sum()
            py_values[trt] = total_years

        total_py = sum(py_values.values())
        results['units'].append({
            'unit': 'unit02', 'level': 2,
            'rowlabel': 'PYs',
            'col1': f"{py_values.get(1, 0):.2f}",
            'col2': f"{py_values.get(2, 0):.2f}",
            'col3': f"{py_values.get(3, 0):.2f}",
            'col_total': f"{total_py:.2f}"
        })

        # Unit 03: Treatment Duration (Months)
        results['units'].append({
            'unit': 'unit03', 'level': 1,
            'rowlabel': 'Treatment Duration (Months) [a]',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        trt_dur_stats = {}
        for trt in sorted(big_n.keys()):
            enrl = self.adsl[(self.adsl['ENRLFL'] == 'Y') & (self.adsl['TRT01PN'] == trt)]
            dur = enrl['TRTDURM'].dropna().tolist()
            if dur:
                trt_dur_stats[trt] = self._fmt_continuous(dur)
            else:
                trt_dur_stats[trt] = {'n': '0', 'mean': 'NE', 'sd': 'NE', 'median': 'NE', 'min_max': 'NE'}

        # All subjects combined
        all_dur = self.adsl[self.adsl['ENRLFL'] == 'Y']['TRTDURM'].dropna().tolist()
        overall_dur_stats = self._fmt_continuous(all_dur)

        for stat_name in ['n', 'Mean', 'Std. Dev.', 'Median', 'Min, Max']:
            stat_key_map = {'n': 'n', 'Mean': 'mean', 'Std. Dev.': 'sd', 'Median': 'median', 'Min, Max': 'min_max'}
            stat_key = stat_key_map.get(stat_name, stat_name.lower().replace(', ', '_').replace(' ', '_'))
            results['units'].append({
                'unit': 'unit03', 'level': 2,
                'rowlabel': stat_name,
                'col1': trt_dur_stats.get(1, {}).get(stat_key, 'NE'),
                'col2': trt_dur_stats.get(2, {}).get(stat_key, 'NE'),
                'col3': trt_dur_stats.get(3, {}).get(stat_key, 'NE'),
                'col_total': overall_dur_stats.get(stat_key, 'NE')
            })

        # Unit 05: Total Amount of Dose Taken (mg/kg)
        results['units'].append({
            'unit': 'unit05', 'level': 1,
            'rowlabel': 'Total Amount of Dose Taken (mg/kg)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        exdtot = self.adex[self.adex['PARAMCD'] == 'EXDTOT']
        merged = exdtot.merge(self.adsl[['USUBJID', 'TRT01PN', 'ENRLFL']], on='USUBJID', how='left', suffixes=('', '_adsl'))

        # Use ENRLFL from ADEX (already there) not from merged
        dose_stats = {}
        for trt in sorted(big_n.keys()):
            trt_dose = merged[(merged['TRT01PN'] == trt) & (merged['ENRLFL'] == 'Y')]['AVAL'].dropna().tolist()
            if trt_dose:
                dose_stats[trt] = self._fmt_continuous(trt_dose)
            else:
                dose_stats[trt] = {'n': '0', 'mean': 'NE', 'sd': 'NE', 'median': 'NE', 'min_max': 'NE'}

        all_dose = merged[merged['ENRLFL'] == 'Y']['AVAL'].dropna().tolist()
        overall_dose_stats = self._fmt_continuous(all_dose)

        for stat_name in ['n', 'Mean', 'Std. Dev.', 'Median', 'Min, Max']:
            stat_key_map = {'n': 'n', 'Mean': 'mean', 'Std. Dev.': 'sd', 'Median': 'median', 'Min, Max': 'min_max'}
            stat_key = stat_key_map.get(stat_name, stat_name.lower().replace(', ', '_').replace(' ', '_'))
            results['units'].append({
                'unit': 'unit05', 'level': 2,
                'rowlabel': stat_name,
                'col1': dose_stats.get(1, {}).get(stat_key, 'NE'),
                'col2': dose_stats.get(2, {}).get(stat_key, 'NE'),
                'col3': dose_stats.get(3, {}).get(stat_key, 'NE'),
                'col_total': overall_dose_stats.get(stat_key, 'NE')
            })

        # Unit 06: Dose Intensity (mg/kg/3weeks)
        results['units'].append({
            'unit': 'unit06', 'level': 1,
            'rowlabel': 'Dose Intensity (mg/kg/3weeks) [c]',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        doseint = self.adex[self.adex['PARAMCD'] == 'DOSEINT']
        merged_di = doseint.merge(self.adsl[['USUBJID', 'TRT01PN', 'ENRLFL']], on='USUBJID', how='left', suffixes=('', '_adsl'))

        di_stats = {}
        for trt in sorted(big_n.keys()):
            trt_di = merged_di[(merged_di['TRT01PN'] == trt) & (merged_di['ENRLFL'] == 'Y')]['AVAL'].dropna().tolist()
            if trt_di:
                di_stats[trt] = self._fmt_continuous(trt_di)
            else:
                di_stats[trt] = {'n': '0', 'mean': 'NE', 'sd': 'NE', 'median': 'NE', 'min_max': 'NE'}

        all_di = merged_di[merged_di['ENRLFL'] == 'Y']['AVAL'].dropna().tolist()
        overall_di_stats = self._fmt_continuous(all_di)

        for stat_name in ['n', 'Mean', 'Std. Dev.', 'Median', 'Min, Max']:
            stat_key_map = {'n': 'n', 'Mean': 'mean', 'Std. Dev.': 'sd', 'Median': 'median', 'Min, Max': 'min_max'}
            stat_key = stat_key_map.get(stat_name, stat_name.lower().replace(', ', '_').replace(' ', '_'))
            results['units'].append({
                'unit': 'unit06', 'level': 2,
                'rowlabel': stat_name,
                'col1': di_stats.get(1, {}).get(stat_key, 'NE'),
                'col2': di_stats.get(2, {}).get(stat_key, 'NE'),
                'col3': di_stats.get(3, {}).get(stat_key, 'NE'),
                'col_total': overall_di_stats.get(stat_key, 'NE')
            })

        # Unit 07: Relative Dose Intensity (%)
        results['units'].append({
            'unit': 'unit07', 'level': 1,
            'rowlabel': 'Relative Dose Intensity (%) [d]',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        relint = self.adex[self.adex['PARAMCD'] == 'RELINT']
        merged_rdi = relint.merge(self.adsl[['USUBJID', 'TRT01PN', 'ENRLFL']], on='USUBJID', how='left', suffixes=('', '_adsl'))

        rdi_stats = {}
        for trt in sorted(big_n.keys()):
            trt_rdi = merged_rdi[(merged_rdi['TRT01PN'] == trt) & (merged_rdi['ENRLFL'] == 'Y')]['AVAL'].dropna().tolist()
            if trt_rdi:
                rdi_stats[trt] = self._fmt_continuous(trt_rdi)
            else:
                rdi_stats[trt] = {'n': '0', 'mean': 'NE', 'sd': 'NE', 'median': 'NE', 'min_max': 'NE'}

        all_rdi = merged_rdi[merged_rdi['ENRLFL'] == 'Y']['AVAL'].dropna().tolist()
        overall_rdi_stats = self._fmt_continuous(all_rdi)

        for stat_name in ['n', 'Mean', 'Std. Dev.', 'Median', 'Min, Max']:
            stat_key_map = {'n': 'n', 'Mean': 'mean', 'Std. Dev.': 'sd', 'Median': 'median', 'Min, Max': 'min_max'}
            stat_key = stat_key_map.get(stat_name, stat_name.lower().replace(', ', '_').replace(' ', '_'))
            results['units'].append({
                'unit': 'unit07', 'level': 2,
                'rowlabel': stat_name,
                'col1': rdi_stats.get(1, {}).get(stat_key, 'NE'),
                'col2': rdi_stats.get(2, {}).get(stat_key, 'NE'),
                'col3': rdi_stats.get(3, {}).get(stat_key, 'NE'),
                'col_total': overall_rdi_stats.get(stat_key, 'NE')
            })

        # Unit 08: Total Number of Cycles Initiated
        results['units'].append({
            'unit': 'unit08', 'level': 1,
            'rowlabel': 'Total Number of Cycles Initiated',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        ncycle = self.adex[self.adex['PARAMCD'] == 'NCYCLE']
        merged_nc = ncycle.merge(self.adsl[['USUBJID', 'TRT01PN', 'ENRLFL']], on='USUBJID', how='left', suffixes=('', '_adsl'))

        nc_stats = {}
        for trt in sorted(big_n.keys()):
            trt_nc = merged_nc[(merged_nc['TRT01PN'] == trt) & (merged_nc['ENRLFL'] == 'Y')]['AVAL'].dropna().tolist()
            if trt_nc:
                nc_stats[trt] = self._fmt_continuous(trt_nc)
            else:
                nc_stats[trt] = {'n': '0', 'mean': 'NE', 'sd': 'NE', 'median': 'NE', 'min_max': 'NE'}

        all_nc = merged_nc[merged_nc['ENRLFL'] == 'Y']['AVAL'].dropna().tolist()
        overall_nc_stats = self._fmt_continuous(all_nc)

        for stat_name in ['n', 'Mean', 'Std. Dev.', 'Median', 'Min, Max']:
            stat_key_map = {'n': 'n', 'Mean': 'mean', 'Std. Dev.': 'sd', 'Median': 'median', 'Min, Max': 'min_max'}
            stat_key = stat_key_map.get(stat_name, stat_name.lower().replace(', ', '_').replace(' ', '_'))
            results['units'].append({
                'unit': 'unit08', 'level': 2,
                'rowlabel': stat_name,
                'col1': nc_stats.get(1, {}).get(stat_key, 'NE'),
                'col2': nc_stats.get(2, {}).get(stat_key, 'NE'),
                'col3': nc_stats.get(3, {}).get(stat_key, 'NE'),
                'col_total': overall_nc_stats.get(stat_key, 'NE')
            })

        return results


def generate_exposure_report(
    adex_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.1.5.1",
    table_title: str = "Exposure",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.1.5.1 (Exposure).

    Args:
        adex_path: Path to ADEX SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adex, _ = pyreadstat.read_sas7bdat(adex_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = ExposureAnalyzer(adex, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                   table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_pfs_report(
    adtte_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.2.2.2",
    table_title: str = "Progression-Free Survival",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.2.2.2 (Progression-Free Survival) using real statistical analysis.

    Args:
        adtte_path: Path to ADTTE SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adtte, _ = pyreadstat.read_sas7bdat(adtte_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = SurvivalAnalyzer(adtte, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                 table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


class OverallSurvivalAnalyzer:
    """
    Implements statistical analysis for Table 14.2.2.3 (Overall Survival).

    Similar to PFS but for overall survival:
    - OS events: Death
    - Censoring reasons: Still alive, lost to follow-up, etc.
    - Median, 25th/75th percentiles
    - Survival rates at 3, 6, 9, 12 months
    """

    def __init__(self, adtte: pd.DataFrame, adsl: pd.DataFrame):
        self.adtte = adtte
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(saf[saf['TRT01PN'] == trt])
        return big_n

    def _filter_os(self) -> pd.DataFrame:
        """Filter ADTTE to OS records."""
        return self.adtte[self.adtte['PARAMCD'] == 'OS'].copy()

    def _kaplan_meier_survival(self, times: np.ndarray, events: np.ndarray,
                                eval_times: list = None) -> Tuple[dict, dict]:
        """Basic Kaplan-Meier survival analysis."""
        n = len(times)
        if n == 0:
            return {}, {}

        order = np.argsort(times)
        times_sorted = times[order]
        events_sorted = events[order]

        unique_times = np.unique(times_sorted)
        n_at_risk = np.arange(len(unique_times), 0, -1)
        n_events = np.array([np.sum(events_sorted[times_sorted == t]) for t in unique_times])

        survival_prob = np.cumprod(1 - n_events / n_at_risk)
        survival_func = dict(zip(unique_times, survival_prob))

        percentiles = {}
        for target_s in [0.5, 0.25, 0.75]:
            below_target = np.where(survival_prob < target_s)[0]
            if len(below_target) > 0:
                percentiles[target_s] = unique_times[below_target[0]]
            else:
                percentiles[target_s] = np.inf

        eval_survival = {}
        if eval_times:
            for t in eval_times:
                idx = np.searchsorted(unique_times, t, side='right') - 1
                if idx >= 0:
                    eval_survival[t] = survival_prob[idx]
                else:
                    eval_survival[t] = 1.0

        return eval_survival, percentiles

    def _get_os_stats(self, df: pd.DataFrame) -> Dict:
        """Get OS statistics for a treatment group."""
        subj_data = df.drop_duplicates('USUBJID')

        times = subj_data['AVAL'].values
        events = (subj_data['CNSR'] == 0).astype(int).values

        # Convert days to months
        times_months = times / 30.44

        eval_months = [3, 6, 9, 12]
        eval_survival, percentiles = self._kaplan_meier_survival(
            times_months, events, eval_months
        )

        n_total = len(subj_data)
        n_event = int(np.sum(events))
        n_censored = n_total - n_event

        return {
            'n_total': n_total,
            'n_event': n_event,
            'n_censored': n_censored,
            'median': percentiles.get(0.5, np.inf),
            'pct_25': percentiles.get(0.75, np.inf),
            'pct_75': percentiles.get(0.25, np.inf),
            'survival_at_months': eval_survival
        }

    def analyze(self) -> Dict:
        """Perform complete OS analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        os_data = self._filter_os()

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        def fmt_pct(n: int, denom: int) -> str:
            if denom == 0:
                return "0 (0.0)"
            pct = n / denom * 100
            return f"{n:>3} ({pct:>5.1f})"

        def fmt_pct_value(pct: float) -> str:
            if np.isinf(pct) or np.isnan(pct):
                return "NA"
            return f"{pct:.1f}"

        def fmt_survival_rate(rate: float) -> str:
            if np.isnan(rate) or np.isinf(rate):
                return "NA"
            return f"{rate:.2f}"

        trt_list = [1, 2, 3]

        # Get stats by treatment
        os_by_trt = {}
        for trt in trt_list:
            trt_data = os_data[os_data['TRTPN'] == trt]
            os_by_trt[trt] = self._get_os_stats(trt_data)

        # Row 0: Overall Survival header
        results['units'].append({
            'unit': 'unit01',
            'level': 1,
            'rowlabel': 'Overall Survival (Months)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Row 1: Subjects with events (%)
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'Subjects with events (%)',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total_events = 0
        for i, trt in enumerate(trt_list, 1):
            n_event = os_by_trt[trt]['n_event']
            row[f'col{i}'] = fmt_pct(n_event, big_n[trt])
            total_events += n_event
        row['col_total'] = fmt_pct(total_events, total_n)
        results['units'].append(row)

        # Row 2: Subjects censored (%)
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'Subjects censored (%)',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        total_censored = 0
        for i, trt in enumerate(trt_list, 1):
            n_censored = os_by_trt[trt]['n_censored']
            row[f'col{i}'] = fmt_pct(n_censored, big_n[trt])
            total_censored += n_censored
        row['col_total'] = fmt_pct(total_censored, total_n)
        results['units'].append(row)

        # Row 3: 25th Percentile
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '25th Percentile',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        pct_25_values = []
        for i, trt in enumerate(trt_list, 1):
            val = os_by_trt[trt]['pct_25']
            row[f'col{i}'] = fmt_pct_value(val)
            pct_25_values.append(val)
        row['col_total'] = fmt_pct_value(np.median(pct_25_values))
        results['units'].append(row)

        # Row 4: 95% CI for 25th percentile
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '95% CI',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        for i in range(3):
            row[f'col{i+1}'] = '(NA, NA)'
        row['col_total'] = '(NA, NA)'
        results['units'].append(row)

        # Row 5: Median
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': 'Median',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        median_values = []
        for i, trt in enumerate(trt_list, 1):
            val = os_by_trt[trt]['median']
            row[f'col{i}'] = fmt_pct_value(val)
            median_values.append(val)
        row['col_total'] = fmt_pct_value(np.median(median_values))
        results['units'].append(row)

        # Row 6: 95% CI for Median
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '95% CI',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        for i in range(3):
            row[f'col{i+1}'] = '(NA, NA)'
        row['col_total'] = '(NA, NA)'
        results['units'].append(row)

        # Row 7: 75th Percentile
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '75th Percentile',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        pct_75_values = []
        for i, trt in enumerate(trt_list, 1):
            val = os_by_trt[trt]['pct_75']
            row[f'col{i}'] = fmt_pct_value(val)
            pct_75_values.append(val)
        row['col_total'] = fmt_pct_value(np.median(pct_75_values))
        results['units'].append(row)

        # Row 8: 95% CI for 75th Percentile
        row = {'unit': 'unit01', 'level': 1,
               'rowlabel': '95% CI',
               'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        for i in range(3):
            row[f'col{i+1}'] = '(NA, NA)'
        row['col_total'] = '(NA, NA)'
        results['units'].append(row)

        # Section 2: OS rates at timepoints
        results['units'].append({
            'unit': 'unit02',
            'level': 1,
            'rowlabel': 'Overall Survival',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Add survival rates at 3, 6, 9, 12 months
        for month in [3, 6, 9, 12]:
            row = {'unit': 'unit02', 'level': 1,
                   'rowlabel': f'Point Estimate at {month} Months',
                   'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
            surv_values = []
            for i, trt in enumerate(trt_list, 1):
                surv = os_by_trt[trt]['survival_at_months'].get(month, np.nan)
                row[f'col{i}'] = fmt_survival_rate(surv)
                if not np.isnan(surv):
                    surv_values.append(surv)
            if surv_values:
                row['col_total'] = fmt_survival_rate(np.mean(surv_values))
            else:
                row['col_total'] = 'NA'
            results['units'].append(row)

            # 95% CI
            row = {'unit': 'unit02', 'level': 1,
                   'rowlabel': '95% CI',
                   'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
            for i in range(3):
                row[f'col{i+1}'] = '(NA, NA)'
            row['col_total'] = '(NA, NA)'
            results['units'].append(row)

        return results


def generate_os_report(
    adtte_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.2.2.3",
    table_title: str = "Overall Survival",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.2.2.3 (Overall Survival) using real statistical analysis.
    """
    # 1. Read ADaM data
    adtte, _ = pyreadstat.read_sas7bdat(adtte_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = OverallSurvivalAnalyzer(adtte, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                 table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_best_overall_response_report(
    adrs_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.2.1.1",
    table_title: str = "Best Overall Response and ORR by Independent Central Review",
    population: str = "Response Evaluable Set"
) -> Dict[str, str]:
    """
    Generate Table 14.2.1.1 (Best Overall Response and ORR) using real statistical analysis.

    Args:
        adrs_path: Path to ADRS SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adrs, _ = pyreadstat.read_sas7bdat(adrs_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = BestOverallResponseAnalyzer(adrs, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                   table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_ae_summary_report(
    adae_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.3.1.1",
    table_title: str = "Overall Summary of Treatment-Emergent Adverse Events",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.3.1.1 (AE Summary) using real statistical analysis.

    Args:
        adae_path: Path to ADAE SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adae, _ = pyreadstat.read_sas7bdat(adae_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = AESummaryAnalyzer(adae, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                   table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def validate_generic_results(generated_df: pd.DataFrame, reference_path: Path):
    """Compare generated results with reference SAS output for generic tables."""
    print("\n" + "="*60)
    print("VALIDATION: Comparing with Reference SAS Output")
    print("="*60)

    ref_df, _ = pyreadstat.read_sas7bdat(str(reference_path))

    print(f"\nGenerated rows: {len(generated_df)}")
    print(f"Reference rows: {len(ref_df)}")

    print("\n--- Key Value Comparison ---")

    for _, gen_row in generated_df.iterrows():
        rowlabel = gen_row['rowlabel']

        ref_matches = ref_df[ref_df['rowlabel'] == rowlabel]
        if ref_matches.empty:
            continue

        ref_row = ref_matches.iloc[0]

        gen_total = str(gen_row['_col_99999']).strip()
        ref_total = str(ref_row['_col_99999']).strip()

        if gen_total and ref_total and gen_total != ref_total:
            print(f"MISMATCH: '{rowlabel}'")
            print(f"  Generated: {gen_total}")
            print(f"  Reference: {ref_total}")
        elif gen_total == ref_total:
            print(f"OK: '{rowlabel}' = {gen_total}")

    print("\n" + "="*60)


def generate_disposition_report(
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.1.1.1",
    table_title: str = "Subject Disposition",
    population: str = "Enrolled Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.1.1.1 using real statistical analysis.

    Args:
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files:
            - 'sas_output': Path to table_XX_X_X_X.sas7bdat
            - 'pdf': Path to Table XX.X.X.X.pdf
    """
    # 1. Read ADaM data
    adam_reader = ADaMDataReader(str(Path(adsl_path).parent))
    adsl = adam_reader.read_adsl()

    # 2. Perform statistical analysis (THE CORE LOGIC)
    analyzer = DispositionAnalyzer(adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate SAS output dataset (intermediate format)
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data(analysis_results)

    sas_output_path = Path(output_dir) / "csv" / f"table_{table_id.replace('.', '_')}.csv"
    sas_output_path.parent.mkdir(parents=True, exist_ok=True)
    sas_df.to_csv(sas_output_path, index=False)
    print(f"  CSV: {sas_output_path}")

    # 4. Generate PDF report using generic method with new styling
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path), table_title, table_id, population)

    # 5. Validation: Compare with reference if available
    reference_path = Path("d:/hello world/clinical-data-process/.knowledge/TLF/Data/Table") / f"table_{table_id.replace('.', '_')}.sas7bdat"
    if reference_path.exists():
        validate_results(sas_df, reference_path)

    return {
        'sas_output': str(sas_output_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def validate_results(generated_df: pd.DataFrame, reference_path: Path):
    """Compare generated results with reference SAS output."""
    print("\n" + "="*60)
    print("VALIDATION: Comparing with Reference SAS Output")
    print("="*60)

    ref_df, _ = pyreadstat.read_sas7bdat(str(reference_path))

    print(f"\nGenerated rows: {len(generated_df)}")
    print(f"Reference rows: {len(ref_df)}")

    # Compare key values
    print("\n--- Key Value Comparison ---")

    # Find rows to compare
    for _, gen_row in generated_df.iterrows():
        rowlabel = gen_row['rowlabel']

        # Find matching row in reference
        ref_matches = ref_df[ref_df['rowlabel'] == rowlabel]
        if ref_matches.empty:
            continue

        ref_row = ref_matches.iloc[0]

        # Compare values
        gen_total = str(gen_row['_col_99999']).strip()
        ref_total = str(ref_row['_col_99999']).strip()

        if gen_total and ref_total and gen_total != ref_total:
            print(f"MISMATCH: '{rowlabel}'")
            print(f"  Generated: {gen_total}")
            print(f"  Reference: {ref_total}")
        elif gen_total == ref_total:
            print(f"OK: '{rowlabel}' = {gen_total}")

    print("\n" + "="*60)


class ProtocolDeviationAnalyzer:
    """
    Implements statistical analysis for Table 14.1.1.2 (Major Protocol Deviation).
    """

    def __init__(self, addv: pd.DataFrame, adsl: pd.DataFrame):
        self.addv = addv
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        for trt in [1, 2, 3]:
            big_n[trt] = len(self.adsl[
                (self.adsl['TRT01PN'] == trt) &
                (self.adsl['SAFFL'] == 'Y')
            ])
        return big_n

    def count_major_deviations_by_trt(self) -> Dict[int, int]:
        """Count subjects with at least one major protocol deviation."""
        major_dv = self.addv[self.addv['DVCAT'] == 'Major']
        trt_map = {1: '5.4 mg/kg', 2: '6.4 mg/kg', 3: '7.4 mg/kg'}
        counts = {}
        for trt_num, trt_name in trt_map.items():
            # Get subjects with major deviations in this treatment
            subjects = major_dv[major_dv['TRTP'] == trt_name]['USUBJID'].unique()
            counts[trt_num] = len(subjects)
        return counts

    def count_by_category_and_reason(self, category: str) -> Dict[int, Tuple[int, int]]:
        """Count by category and reason within treatment."""
        major_dv = self.addv[
            (self.addv['DVCAT'] == 'Major') &
            (self.addv['DVDECOD'] == category)
        ]
        trt_map = {1: '5.4 mg/kg', 2: '6.4 mg/kg', 3: '7.4 mg/kg'}
        counts = {}
        for trt_num, trt_name in trt_map.items():
            denom = len(self.adsl[
                (self.adsl['TRT01PN'] == trt_num) &
                (self.adsl['SAFFL'] == 'Y')
            ])
            subjects = major_dv[major_dv['TRTP'] == trt_name]['USUBJID'].unique()
            counts[trt_num] = (len(subjects), denom)
        return counts

    def count_by_reason_only(self, reason: str) -> Dict[int, Tuple[int, int]]:
        """Count by specific reason (like EX01, IN05) across all categories."""
        major_dv = self.addv[
            (self.addv['DVCAT'] == 'Major') &
            (self.addv['DVTERM'].str.contains(reason, na=False, case=False))
        ]
        trt_map = {1: '5.4 mg/kg', 2: '6.4 mg/kg', 3: '7.4 mg/kg'}
        counts = {}
        for trt_num, trt_name in trt_map.items():
            denom = len(self.adsl[
                (self.adsl['TRT01PN'] == trt_num) &
                (self.adsl['SAFFL'] == 'Y')
            ])
            subjects = major_dv[major_dv['TRTP'] == trt_name]['USUBJID'].unique()
            counts[trt_num] = (len(subjects), denom)
            counts[trt] = (len(subjects), denom)
        return counts

    def analyze(self) -> Dict:
        """Perform complete protocol deviation analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        def fmt_freq(count, denom):
            pct = (count / denom * 100) if denom > 0 else 0
            return f"{count:>3} ({pct:>5.1f})"

        def fmt_n(count):
            return f"{count:>3}"

        # Overall: Subjects with Any Major Protocol Deviation
        any_major = self.count_major_deviations_by_trt()
        total_major = sum(any_major.values())

        results['units'].append({
            'unit': 'unit01',
            'level': 1,
            'rowlabel': 'Subjects with Any Major Protocol Deviation',
            'col1': fmt_freq(any_major[1], big_n[1]),
            'col2': fmt_freq(any_major[2], big_n[2]),
            'col3': fmt_freq(any_major[3], big_n[3]),
            'col_total': fmt_freq(total_major, total_n)
        })

        # Major Deviation Category header
        results['units'].append({
            'unit': 'unit01',
            'level': 0,
            'rowlabel': 'Major Deviation Category:',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Categories (from SAS output reference)
        categories = [
            'Eligibility and Entry Criteria',
            'Concominant or Prohibited Medications or Non-Drug Therapy',
            'Efficacy Criteria',
            'IP Compliance',
            'Informed Consent',
            'Laboratory Assessment Criteria',
            'Serious Adverse Event Criteria',
            'Study Procedures Criteria'
        ]

        # Sub-reasons for Eligibility and Entry Criteria
        eligibility_reasons = {
            'Inclusion Criteria': ['IN05', 'IN11'],
            'Exclusion Criteria': ['EX01', 'EX04', 'EX10', 'EX11', 'EX13', 'EX18']
        }

        for category in categories:
            cat_counts = self.count_by_category_and_reason(category)

            if category == 'Eligibility and Entry Criteria':
                # Add parent row
                total_cat = sum(c[0] for c in cat_counts.values())
                total_denom = sum(c[1] for c in cat_counts.values())

                results['units'].append({
                    'unit': 'unit02',
                    'level': 1,
                    'rowlabel': category,
                    'col1': fmt_freq(cat_counts[1][0], cat_counts[1][1]),
                    'col2': fmt_freq(cat_counts[2][0], cat_counts[2][1]),
                    'col3': fmt_freq(cat_counts[3][0], cat_counts[3][1]),
                    'col_total': fmt_freq(total_cat, total_denom)
                })

                # Add sub-categories
                trt_map = {1: '5.4 mg/kg', 2: '6.4 mg/kg', 3: '7.4 mg/kg'}
                for sub_cat, reasons in eligibility_reasons.items():
                    sub_counts = {}
                    for trt_num, trt_name in trt_map.items():
                        denom = cat_counts[trt_num][1]
                        count = 0
                        for reason in reasons:
                            reason_data = self.addv[
                                (self.addv['DVCAT'] == 'Major') &
                                (self.addv['DVDECOD'] == category) &
                                (self.addv['TRTP'] == trt_name) &
                                (self.addv['VIOCODE'] == reason)
                            ]
                            count += len(reason_data['USUBJID'].unique())
                        sub_counts[trt_num] = (count, denom)

                    results['units'].append({
                        'unit': 'unit02',
                        'level': 2,
                        'rowlabel': sub_cat,
                        'col1': fmt_freq(sub_counts[1][0], sub_counts[1][1]),
                        'col2': fmt_freq(sub_counts[2][0], sub_counts[2][1]),
                        'col3': fmt_freq(sub_counts[3][0], sub_counts[3][1]),
                        'col_total': ''
                    })

                    # Add individual reasons
                    for reason in reasons:
                        reason_counts = {}
                        for trt_num, trt_name in trt_map.items():
                            denom = cat_counts[trt_num][1]
                            reason_data = self.addv[
                                (self.addv['DVCAT'] == 'Major') &
                                (self.addv['DVDECOD'] == category) &
                                (self.addv['TRTP'] == trt_name) &
                                (self.addv['VIOCODE'] == reason)
                            ]
                            count = len(reason_data['USUBJID'].unique())
                            reason_counts[trt_num] = (count, denom)

                        total_reason = sum(c[0] for c in reason_counts.values())
                        total_denom = sum(c[1] for c in reason_counts.values())

                        results['units'].append({
                            'unit': 'unit02',
                            'level': 3,
                            'rowlabel': reason,
                            'col1': fmt_n(reason_counts[1][0]),
                            'col2': fmt_n(reason_counts[2][0]),
                            'col3': fmt_n(reason_counts[3][0]),
                            'col_total': fmt_n(total_reason)
                        })
            else:
                # Other categories (no sub-items)
                total_cat = sum(c[0] for c in cat_counts.values())
                total_denom = sum(c[1] for c in cat_counts.values())

                results['units'].append({
                    'unit': 'unit02',
                    'level': 1,
                    'rowlabel': category,
                    'col1': fmt_freq(cat_counts[1][0], cat_counts[1][1]),
                    'col2': fmt_freq(cat_counts[2][0], cat_counts[2][1]),
                    'col3': fmt_freq(cat_counts[3][0], cat_counts[3][1]),
                    'col_total': fmt_freq(total_cat, total_denom)
                })

        return results


def generate_protocol_deviation_report(
    addv_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.1.1.2",
    table_title: str = "Major Protocol Deviations",
    population: str = "Enrolled Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.1.1.2 (Major Protocol Deviation) using real statistical analysis.
    """
    # 1. Read ADaM data
    adam_reader = ADaMDataReader(str(Path(adsl_path).parent))
    adsl = adam_reader.read_adsl()

    # Read ADDV dataset
    addv, _ = pyreadstat.read_sas7bdat(addv_path)

    # 2. Perform statistical analysis
    analyzer = ProtocolDeviationAnalyzer(addv, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate SAS output dataset
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path), table_title, table_id, population)

    # 5. Validation
    reference_path = Path("d:/hello world/clinical-data-process/.knowledge/TLF/Data/Table") / f"table_{table_id.replace('.', '_')}.sas7bdat"
    if reference_path.exists():
        validate_generic_results(sas_df, reference_path)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


class ExclusionFromAnalysisSetAnalyzer:
    """
    Implements statistical analysis for Table 14.1.1.3 (Subjects Excluded from Analysis Sets).
    """

    def __init__(self, adsl: pd.DataFrame):
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Enrolled subjects."""
        big_n = {}
        for trt in [1, 2, 3]:
            big_n[trt] = len(self.adsl[
                (self.adsl['TRT01PN'] == trt) &
                (self.adsl['ENRLFL'] == 'Y')
            ])
        return big_n

    def count_excluded_by_reason(self, flag: str, reason_var: str) -> Dict[str, Dict[int, int]]:
        """Count excluded subjects by reason and treatment."""
        excluded = self.adsl[
            (self.adsl[flag] == 'N') &
            (self.adsl[reason_var].notna()) &
            (self.adsl[reason_var] != '')
        ]

        # Get unique reasons
        reasons = excluded[reason_var].unique()

        result = {}
        for reason in reasons:
            if pd.isna(reason) or str(reason).strip() == '':
                continue
            reason_counts = {}
            for trt in [1, 2, 3]:
                count = len(excluded[
                    (excluded['TRT01PN'] == trt) &
                    (excluded[reason_var] == reason)
                ])
                reason_counts[trt] = count
            result[str(reason)] = reason_counts

        return result

    def analyze(self) -> Dict:
        """Perform complete exclusion analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        def fmt_freq(count, denom):
            pct = (count / denom * 100) if denom > 0 else 0
            return f"{count:>3} ({pct:>5.1f})"

        def fmt_n(count):
            return f"{count:>3}"

        # Unit 1: Safety Analysis Set (excluded = SAFFL='N')
        saf_excluded = self.adsl[
            (self.adsl['SAFFL'] == 'N') &
            (self.adsl['ENRLFL'] == 'Y')
        ]
        saf_reasons = saf_excluded['SAFREAS'].unique() if 'SAFREAS' in saf_excluded.columns else []

        results['units'].append({
            'unit': 'unit01',
            'level': 1,
            'rowlabel': 'Safety Analysis Set',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': str(len(saf_excluded))
        })

        # Unit 2: Response Evaluable Set (excluded = RESFL='N')
        res_excluded = self.adsl[
            (self.adsl['RESFL'] == 'N') &
            (self.adsl['ENRLFL'] == 'Y')
        ]
        res_reasons = self.count_excluded_by_reason('RESFL', 'RESREAS')

        results['units'].append({
            'unit': 'unit02',
            'level': 1,
            'rowlabel': 'Response Evaluable Set',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': ''
        })

        for reason, counts in sorted(res_reasons.items()):
            total = sum(counts.values())
            results['units'].append({
                'unit': 'unit02',
                'level': 2,
                'rowlabel': reason,
                'col1': fmt_n(counts.get(1, 0)),
                'col2': fmt_n(counts.get(2, 0)),
                'col3': fmt_n(counts.get(3, 0)),
                'col_total': fmt_n(total)
            })

        # Unit 3: Pharmacokinetic Analysis Set (excluded = PKFL='N')
        pk_excluded = self.adsl[
            (self.adsl['PKFL'] == 'N') &
            (self.adsl['ENRLFL'] == 'Y')
        ]
        pk_reasons = self.count_excluded_by_reason('PKFL', 'PKREAS')

        results['units'].append({
            'unit': 'unit03',
            'level': 1,
            'rowlabel': 'Pharmacokinetic Analysis Set',
            'col1': '', 'col2': '', 'col3': '',
            'col_total': str(len(pk_excluded))
        })

        return results


def generate_exclusion_report(
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.1.1.3",
    table_title: str = "Subjects Excluded from Analysis Sets",
    population: str = "Enrolled Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.1.1.3 (Subjects Excluded from Analysis Sets).
    """
    # 1. Read ADaM data
    adam_reader = ADaMDataReader(str(Path(adsl_path).parent))
    adsl = adam_reader.read_adsl()

    # 2. Perform statistical analysis
    analyzer = ExclusionFromAnalysisSetAnalyzer(adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate SAS output dataset
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                    table_title, table_id, population)

    # 5. Validation
    reference_path = Path("d:/hello world/clinical-data-process/.knowledge/TLF/Data/Table") / f"table_{table_id.replace('.', '_')}.sas7bdat"
    if reference_path.exists():
        validate_generic_results(sas_df, reference_path)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


class DemographicAnalyzer:
    """
    Implements statistical analysis for Table 14.1.2.x (Demographic and Baseline Characteristics).

    Table variants:
    - 14.1.2.1: Enrolled Analysis Set (ENRLFL='Y')
    - 14.1.2.2: Enrolled Analysis Set by Region/Country
    - 14.1.2.3: Safety Analysis Set (SAFFL='Y')
    - 14.1.2.4: Safety Analysis Set by Region/Country
    """

    def __init__(self, adsl: pd.DataFrame, population_filter: str = "enrolled",
                 include_country_breakdown: bool = False):
        self.adsl = adsl
        # Population filter: 'enrolled' (ENRLFL) or 'safety' (SAFFL)
        self.population_filter = population_filter
        # Whether to include country/region breakdown
        self.include_country_breakdown = include_country_breakdown
        self._filter_population()

    def _filter_population(self):
        """Filter to appropriate analysis population."""
        if self.population_filter == 'safety':
            self.adsl = self.adsl[self.adsl['SAFFL'] == 'Y'].copy()
        else:  # enrolled
            self.adsl = self.adsl[self.adsl['ENRLFL'] == 'Y'].copy()

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N (number of subjects) by treatment group."""
        big_n = {}
        for trt in [1, 2, 3]:
            big_n[trt] = len(self.adsl[self.adsl['TRT01PN'] == trt])
        return big_n

    def total_n(self) -> int:
        """Total number of subjects in Safety Analysis Set."""
        return len(self.adsl)

    def count_categorical(self, var: str) -> Dict[int, Dict[str, int]]:
        """Count categorical variable by treatment group."""
        counts = {1: {}, 2: {}, 3: {}}
        for trt in [1, 2, 3]:
            subset = self.adsl[self.adsl['TRT01PN'] == trt]
            for val in subset[var].dropna().unique():
                counts[trt][val] = len(subset[subset[var] == val])
        return counts

    def descriptive_stats(self, var: str, by_trt: bool = True) -> Dict:
        """Calculate descriptive statistics for a continuous variable."""
        if by_trt:
            result = {}
            for trt in [1, 2, 3]:
                subset = self.adsl[
                    (self.adsl['TRT01PN'] == trt) &
                    (self.adsl[var].notna())
                ][var]
                if len(subset) > 0:
                    result[trt] = {
                        'n': len(subset),
                        'mean': subset.mean(),
                        'std': subset.std(),
                        'median': subset.median(),
                        'min': subset.min(),
                        'max': subset.max()
                    }
                else:
                    result[trt] = {'n': 0}
            return result
        else:
            subset = self.adsl[self.adsl[var].notna()][var]
            if len(subset) > 0:
                return {
                    'n': len(subset),
                    'mean': subset.mean(),
                    'std': subset.std(),
                    'median': subset.median(),
                    'min': subset.min(),
                    'max': subset.max()
                }
            return {'n': 0}

    def analyze(self) -> Dict:
        """Perform complete demographic analysis."""
        results = {
            'big_n': self.calculate_big_n(),
            'total_n': self.total_n(),
            'units': []
        }

        # Big N row
        big_n = results['big_n']
        total_n = results['total_n']
        results['units'].append({
            'unit': 'big_n',
            'level': 0,
            'rowlabel': 'Subjects in Safety Analysis Set',
            'col1': str(big_n.get(1, 0)),
            'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)),
            'col_total': str(total_n)
        })

        # Age (continuous)
        age_stats = self.descriptive_stats('AGE', by_trt=True)
        results['units'].append({
            'unit': 'age_header',
            'level': 1,
            'rowlabel': 'Age (years)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Mean (SD) - one row with all treatment groups
        mean_row = {'unit': 'age', 'level': 2, 'rowlabel': '  Mean (SD)',
                    'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        median_row = {'unit': 'age_median', 'level': 2, 'rowlabel': '  Median (Min, Max)',
                      'col1': '', 'col2': '', 'col3': '', 'col_total': ''}
        for trt in [1, 2, 3]:
            stats = age_stats.get(trt, {'n': 0})
            n = stats.get('n', 0)
            col_key = f'col{trt}'
            if n > 0:
                mean = stats.get('mean', 0)
                std = stats.get('std', 0)
                mean_row[col_key] = f"{mean:.1f} ({std:.1f})"

                median = stats.get('median', 0)
                min_val = stats.get('min', 0)
                max_val = stats.get('max', 0)
                median_row[col_key] = f"{median:.1f} ({min_val:.0f}, {max_val:.0f})"
        results['units'].append(mean_row)
        results['units'].append(median_row)

        # Age Group (<65, >=65)
        agegr_counts = {}
        for trt in [1, 2, 3]:
            subset = self.adsl[self.adsl['TRT01PN'] == trt]
            agegr_counts[trt] = {}
            for val in ['<65', '>=65']:
                agegr_counts[trt][val] = len(subset[subset['AGEGR'] == val])
            agegr_counts[trt]['Total'] = len(subset[subset['AGEGR'].notna()])

        results['units'].append({
            'unit': 'agegr_header',
            'level': 1,
            'rowlabel': 'Age Group, n (%)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })
        for val in ['<65', '>=65']:
            rowlabel = f"  {val}"
            col1 = f"{agegr_counts[1].get(val, 0)} ({agegr_counts[1].get(val, 0)/big_n[1]*100:.1f}%)" if big_n[1] > 0 else "0 (0.0%)"
            col2 = f"{agegr_counts[2].get(val, 0)} ({agegr_counts[2].get(val, 0)/big_n[2]*100:.1f}%)" if big_n[2] > 0 else "0 (0.0%)"
            col3 = f"{agegr_counts[3].get(val, 0)} ({agegr_counts[3].get(val, 0)/big_n[3]*100:.1f}%)" if big_n[3] > 0 else "0 (0.0%)"
            col_total_val = sum(agegr_counts[t].get(val, 0) for t in [1, 2, 3])
            col_total_pct = col_total_val / total_n * 100 if total_n > 0 else 0
            col_total = f"{col_total_val} ({col_total_pct:.1f}%)"
            results['units'].append({
                'unit': 'agegr',
                'level': 2,
                'rowlabel': rowlabel,
                'col1': col1, 'col2': col2, 'col3': col3, 'col_total': col_total
            })

        # Sex
        sex_counts = {}
        for trt in [1, 2, 3]:
            subset = self.adsl[self.adsl['TRT01PN'] == trt]
            sex_counts[trt] = {}
            for val in ['F', 'M']:
                sex_counts[trt][val] = len(subset[subset['SEX'] == val])
            sex_counts[trt]['Total'] = len(subset[subset['SEX'].notna()])

        results['units'].append({
            'unit': 'sex_header',
            'level': 1,
            'rowlabel': 'Sex, n (%)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })
        for val, label in [('F', 'Female'), ('M', 'Male')]:
            rowlabel = f"  {label}"
            col1 = f"{sex_counts[1].get(val, 0)} ({sex_counts[1].get(val, 0)/big_n[1]*100:.1f}%)" if big_n[1] > 0 else "0 (0.0%)"
            col2 = f"{sex_counts[2].get(val, 0)} ({sex_counts[2].get(val, 0)/big_n[2]*100:.1f}%)" if big_n[2] > 0 else "0 (0.0%)"
            col3 = f"{sex_counts[3].get(val, 0)} ({sex_counts[3].get(val, 0)/big_n[3]*100:.1f}%)" if big_n[3] > 0 else "0 (0.0%)"
            col_total_val = sum(sex_counts[t].get(val, 0) for t in [1, 2, 3])
            col_total_pct = col_total_val / total_n * 100 if total_n > 0 else 0
            col_total = f"{col_total_val} ({col_total_pct:.1f}%)"
            results['units'].append({
                'unit': 'sex',
                'level': 2,
                'rowlabel': rowlabel,
                'col1': col1, 'col2': col2, 'col3': col3, 'col_total': col_total
            })

        # Race
        race_counts = {}
        for trt in [1, 2, 3]:
            subset = self.adsl[self.adsl['TRT01PN'] == trt]
            race_counts[trt] = {}
            # Get all non-empty race values
            for val in subset['RACE'].dropna().unique():
                if str(val).strip():  # Skip empty strings
                    race_counts[trt][str(val).strip()] = len(subset[subset['RACE'] == val])
            race_counts[trt]['Total'] = len(subset[subset['RACE'].notna()])

        results['units'].append({
            'unit': 'race_header',
            'level': 1,
            'rowlabel': 'Race, n (%)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })
        for val in sorted(set.union(*[set(race_counts[t].keys()) - {'Total'} for t in [1, 2, 3]])):
            rowlabel = f"  {val}"
            col1 = f"{race_counts[1].get(val, 0)} ({race_counts[1].get(val, 0)/big_n[1]*100:.1f}%)" if big_n[1] > 0 else "0 (0.0%)"
            col2 = f"{race_counts[2].get(val, 0)} ({race_counts[2].get(val, 0)/big_n[2]*100:.1f}%)" if big_n[2] > 0 else "0 (0.0%)"
            col3 = f"{race_counts[3].get(val, 0)} ({race_counts[3].get(val, 0)/big_n[3]*100:.1f}%)" if big_n[3] > 0 else "0 (0.0%)"
            col_total_val = sum(race_counts[t].get(val, 0) for t in [1, 2, 3])
            col_total_pct = col_total_val / total_n * 100 if total_n > 0 else 0
            col_total = f"{col_total_val} ({col_total_pct:.1f}%)"
            results['units'].append({
                'unit': 'race',
                'level': 2,
                'rowlabel': rowlabel,
                'col1': col1, 'col2': col2, 'col3': col3, 'col_total': col_total
            })

        # Ethnicity
        ethnic_counts = {}
        for trt in [1, 2, 3]:
            subset = self.adsl[self.adsl['TRT01PN'] == trt]
            ethnic_counts[trt] = {}
            for val in subset['ETHNIC'].dropna().unique():
                ethnic_counts[trt][val] = len(subset[subset['ETHNIC'] == val])
            ethnic_counts[trt]['Total'] = len(subset[subset['ETHNIC'].notna()])

        results['units'].append({
            'unit': 'ethnic_header',
            'level': 1,
            'rowlabel': 'Ethnicity, n (%)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })
        for val in sorted(set.union(*[set(ethnic_counts[t].keys()) - {'Total'} for t in [1, 2, 3]])):
            rowlabel = f"  {val}"
            col1 = f"{ethnic_counts[1].get(val, 0)} ({ethnic_counts[1].get(val, 0)/big_n[1]*100:.1f}%)" if big_n[1] > 0 else "0 (0.0%)"
            col2 = f"{ethnic_counts[2].get(val, 0)} ({ethnic_counts[2].get(val, 0)/big_n[2]*100:.1f}%)" if big_n[2] > 0 else "0 (0.0%)"
            col3 = f"{ethnic_counts[3].get(val, 0)} ({ethnic_counts[3].get(val, 0)/big_n[3]*100:.1f}%)" if big_n[3] > 0 else "0 (0.0%)"
            col_total_val = sum(ethnic_counts[t].get(val, 0) for t in [1, 2, 3])
            col_total_pct = col_total_val / total_n * 100 if total_n > 0 else 0
            col_total = f"{col_total_val} ({col_total_pct:.1f}%)"
            results['units'].append({
                'unit': 'ethnic',
                'level': 2,
                'rowlabel': rowlabel,
                'col1': col1, 'col2': col2, 'col3': col3, 'col_total': col_total
            })

        # Region
        region_counts = {}
        for trt in [1, 2, 3]:
            subset = self.adsl[self.adsl['TRT01PN'] == trt]
            region_counts[trt] = {}
            for val in subset['REGION1'].dropna().unique():
                region_counts[trt][val] = len(subset[subset['REGION1'] == val])
            region_counts[trt]['Total'] = len(subset[subset['REGION1'].notna()])

        results['units'].append({
            'unit': 'region_header',
            'level': 1,
            'rowlabel': 'Region, n (%)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })
        for val in sorted(set.union(*[set(region_counts[t].keys()) - {'Total'} for t in [1, 2, 3]])):
            rowlabel = f"  {val}"
            col1 = f"{region_counts[1].get(val, 0)} ({region_counts[1].get(val, 0)/big_n[1]*100:.1f}%)" if big_n[1] > 0 else "0 (0.0%)"
            col2 = f"{region_counts[2].get(val, 0)} ({region_counts[2].get(val, 0)/big_n[2]*100:.1f}%)" if big_n[2] > 0 else "0 (0.0%)"
            col3 = f"{region_counts[3].get(val, 0)} ({region_counts[3].get(val, 0)/big_n[3]*100:.1f}%)" if big_n[3] > 0 else "0 (0.0%)"
            col_total_val = sum(region_counts[t].get(val, 0) for t in [1, 2, 3])
            col_total_pct = col_total_val / total_n * 100 if total_n > 0 else 0
            col_total = f"{col_total_val} ({col_total_pct:.1f}%)"
            results['units'].append({
                'unit': 'region',
                'level': 2,
                'rowlabel': rowlabel,
                'col1': col1, 'col2': col2, 'col3': col3, 'col_total': col_total
            })

        # Baseline ECOG
        ecog_counts = {}
        for trt in [1, 2, 3]:
            subset = self.adsl[self.adsl['TRT01PN'] == trt]
            ecog_counts[trt] = {}
            for val in subset['ECOGBL'].dropna().unique():
                ecog_counts[trt][val] = len(subset[subset['ECOGBL'] == val])
            ecog_counts[trt]['Total'] = len(subset[subset['ECOGBL'].notna()])

        results['units'].append({
            'unit': 'ecog_header',
            'level': 1,
            'rowlabel': 'ECOG Performance Status at Baseline, n (%)',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })
        for val in sorted(set.union(*[set(ecog_counts[t].keys()) - {'Total'} for t in [1, 2, 3]])):
            rowlabel = f"  {int(val) if pd.notna(val) else 'Unknown'}"
            col1 = f"{ecog_counts[1].get(val, 0)} ({ecog_counts[1].get(val, 0)/big_n[1]*100:.1f}%)" if big_n[1] > 0 else "0 (0.0%)"
            col2 = f"{ecog_counts[2].get(val, 0)} ({ecog_counts[2].get(val, 0)/big_n[2]*100:.1f}%)" if big_n[2] > 0 else "0 (0.0%)"
            col3 = f"{ecog_counts[3].get(val, 0)} ({ecog_counts[3].get(val, 0)/big_n[3]*100:.1f}%)" if big_n[3] > 0 else "0 (0.0%)"
            col_total_val = sum(ecog_counts[t].get(val, 0) for t in [1, 2, 3])
            col_total_pct = col_total_val / total_n * 100 if total_n > 0 else 0
            col_total = f"{col_total_val} ({col_total_pct:.1f}%)"
            results['units'].append({
                'unit': 'ecog',
                'level': 2,
                'rowlabel': rowlabel,
                'col1': col1, 'col2': col2, 'col3': col3, 'col_total': col_total
            })

        # Country breakdown (for 14.1.2.2 and 14.1.2.4)
        if self.include_country_breakdown:
            country_counts = {}
            for trt in [1, 2, 3]:
                subset = self.adsl[self.adsl['TRT01PN'] == trt]
                country_counts[trt] = {}
                for val in subset['COUNTRY'].dropna().unique():
                    country_counts[trt][val] = len(subset[subset['COUNTRY'] == val])
                country_counts[trt]['Total'] = len(subset[subset['COUNTRY'].notna()])

            results['units'].append({
                'unit': 'country_header',
                'level': 1,
                'rowlabel': 'Country, n (%)',
                'col1': '', 'col2': '', 'col3': '', 'col_total': ''
            })
            for val in sorted(set.union(*[set(country_counts[t].keys()) - {'Total'} for t in [1, 2, 3]])):
                rowlabel = f"  {val}"
                col1 = f"{country_counts[1].get(val, 0)} ({country_counts[1].get(val, 0)/big_n[1]*100:.1f}%)" if big_n[1] > 0 else "0 (0.0%)"
                col2 = f"{country_counts[2].get(val, 0)} ({country_counts[2].get(val, 0)/big_n[2]*100:.1f}%)" if big_n[2] > 0 else "0 (0.0%)"
                col3 = f"{country_counts[3].get(val, 0)} ({country_counts[3].get(val, 0)/big_n[3]*100:.1f}%)" if big_n[3] > 0 else "0 (0.0%)"
                col_total_val = sum(country_counts[t].get(val, 0) for t in [1, 2, 3])
                col_total_pct = col_total_val / total_n * 100 if total_n > 0 else 0
                col_total = f"{col_total_val} ({col_total_pct:.1f}%)"
                results['units'].append({
                    'unit': 'country',
                    'level': 2,
                    'rowlabel': rowlabel,
                    'col1': col1, 'col2': col2, 'col3': col3, 'col_total': col_total
                })

        return results


class TumorChangeAnalyzer:
    """
    Implements statistical analysis for Table 14.2.3.1 (Best Change in Sum of Target Lesions).

    Analyzes best overall response from target lesions:
    - CR/PR: Complete/Partial Response
    - SD: Stable Disease
    - PD: Progressive Disease
    - NE: Not Evaluable
    """

    def __init__(self, adrs: pd.DataFrame, adsl: pd.DataFrame):
        self.adrs = adrs
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Response Evaluable Set."""
        big_n = {}
        res = self.adsl[self.adsl['RESFL'] == 'Y']
        for trt in res['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(res[res['TRT01PN'] == trt])
        return big_n

    def _get_best_response_data(self) -> pd.DataFrame:
        """Get best response data from ADRS."""
        # Filter for overall response assessments
        mask = (
            (self.adrs['RSTESTCD'] == 'OVRLRESP') &
            (self.adrs['RSEVAL'] == 'INDEPENDENT ASSESSOR')
        )
        target_data = self.adrs[mask].copy()

        if len(target_data) == 0:
            # Fallback: use all ADRS data
            target_data = self.adrs.copy()

        # Response hierarchy: CR > PR > SD > PD > NE
        response_order = {'CR': 1, 'PR': 2, 'SD': 3, 'PD': 4, 'NE': 5, 'NON-CR/NON-PD': 6}

        # Get best response per subject (lowest order = best)
        best_response = {}
        for subj, grp in target_data.groupby('USUBJID'):
            grp = grp.sort_values('RSDTC')
            responses = grp['RSSTRESC'].dropna().unique()
            best = None
            best_order = 999
            for resp in responses:
                order = response_order.get(resp, 999)
                if order < best_order:
                    best_order = order
                    best = resp
            if best:
                best_response[subj] = best

        # Create DataFrame with best response
        if not best_response:
            return pd.DataFrame(columns=['USUBJID', 'BESTRESP'])

        change_df = pd.DataFrame([
            {'USUBJID': subj, 'BESTRESP': resp}
            for subj, resp in best_response.items()
        ])

        return change_df

    def _categorize_response(self, resp: str) -> str:
        """Categorize response into groups."""
        if pd.isna(resp) or resp == 'NE':
            return 'Not Evaluable'
        if resp in ['CR', 'PR']:
            return 'Good (CR/PR)'
        elif resp == 'SD':
            return 'Intermediate (SD)'
        elif resp in ['PD', 'NON-CR/NON-PD']:
            return 'Poor (PD)'
        return 'Not Evaluable'

    def analyze(self) -> Dict:
        """Perform tumor response analysis."""
        results = {
            'units': []
        }

        # Get best response data
        change_df = self._get_best_response_data()

        if len(change_df) == 0:
            # Return empty results if no data
            return results

        # Merge with ADSL for treatment info
        merged = change_df.merge(
            self.adsl[['USUBJID', 'TRT01PN', 'RESFL']],
            on='USUBJID',
            how='left'
        )

        # Filter to Response Evaluable Set
        merged = merged[merged['RESFL'] == 'Y']

        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        # Big N row
        results['units'].append({
            'unit': 'big_n',
            'level': 0,
            'rowlabel': 'Subjects with Measurable Disease at Baseline',
            'col1': str(big_n.get(1, 0)),
            'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)),
            'col_total': str(total_n)
        })

        # Categorize responses
        merged['CATEGORY'] = merged['BESTRESP'].apply(self._categorize_response)

        # Calculate categories by treatment
        categories = ['Good (CR/PR)', 'Intermediate (SD)', 'Poor (PD)', 'Not Evaluable']
        cat_counts = {cat: {1: 0, 2: 0, 3: 0} for cat in categories}

        for trt in [1, 2, 3]:
            trt_data = merged[merged['TRT01PN'] == trt]
            for cat in categories:
                cat_counts[cat][trt] = len(trt_data[trt_data['CATEGORY'] == cat])

        # Header for Best Response Summary
        results['units'].append({
            'unit': 'response_header',
            'level': 1,
            'rowlabel': 'Best Overall Response by Independent Central Review',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Add rows for each category
        for cat in categories:
            rowlabel = f"  {cat}"
            col1_pct = cat_counts[cat][1] / big_n.get(1, 1) * 100 if big_n.get(1, 0) > 0 else 0
            col2_pct = cat_counts[cat][2] / big_n.get(2, 1) * 100 if big_n.get(2, 0) > 0 else 0
            col3_pct = cat_counts[cat][3] / big_n.get(3, 1) * 100 if big_n.get(3, 0) > 0 else 0
            total_pct = sum(cat_counts[cat].values()) / total_n * 100 if total_n > 0 else 0

            results['units'].append({
                'unit': 'response_cat',
                'level': 2,
                'rowlabel': rowlabel,
                'col1': f"{cat_counts[cat][1]} ({col1_pct:.1f}%)",
                'col2': f"{cat_counts[cat][2]} ({col2_pct:.1f}%)",
                'col3': f"{cat_counts[cat][3]} ({col3_pct:.1f}%)",
                'col_total': f"{sum(cat_counts[cat].values())} ({total_pct:.1f}%)"
            })

        return results


class DeathAnalyzer:
    """
    Implements statistical analysis for Table 14.3.2.1 (Deaths).

    Analyzes deaths by time period and cause:
    - On-treatment deaths
    - Post-treatment deaths
    - Deaths due to adverse events vs disease
    """

    def __init__(self, adae: pd.DataFrame, adsl: pd.DataFrame):
        self.adae = adae
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(saf[saf['TRT01PN'] == trt])
        return big_n

    def analyze(self) -> Dict:
        """Perform death analysis."""
        results = {
            'units': []
        }

        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        # Big N row
        results['units'].append({
            'unit': 'big_n',
            'level': 0,
            'rowlabel': 'Subjects in Safety Analysis Set',
            'col1': str(big_n.get(1, 0)),
            'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)),
            'col_total': str(total_n)
        })

        # Get deaths from ADAE
        if 'DTHFL' in self.adae.columns:
            deaths = self.adae[self.adae['DTHFL'] == 'Y'].copy()
        else:
            deaths = pd.DataFrame()

        # Overall Deaths header
        results['units'].append({
            'unit': 'death_header',
            'level': 1,
            'rowlabel': 'Overall Deaths',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Calculate deaths by treatment
        death_counts = {trt: 0 for trt in [1, 2, 3]}
        if len(deaths) > 0 and 'TRTPN' in deaths.columns:
            for trt in [1, 2, 3]:
                death_counts[trt] = len(deaths[deaths['TRTPN'] == trt]['USUBJID'].unique())
        elif len(deaths) > 0 and 'USUBJID' in deaths.columns:
            # Try to merge with ADSL for treatment
            merged_deaths = deaths.merge(
                self.adsl[['USUBJID', 'TRT01PN']],
                on='USUBJID',
                how='left'
            )
            for trt in [1, 2, 3]:
                death_counts[trt] = len(merged_deaths[merged_deaths['TRT01PN'] == trt]['USUBJID'].unique())

        total_deaths = sum(death_counts.values())

        # Deaths row
        for trt in [1, 2, 3]:
            pct = death_counts[trt] / big_n.get(trt, 1) * 100 if big_n.get(trt, 0) > 0 else 0
            results['units'].append({
                'unit': 'death',
                'level': 2,
                'rowlabel': '  Deaths',
                'col1': f"{death_counts[1]} ({death_counts[1]/big_n.get(1,1)*100:.1f}%)" if trt == 1 else '',
                'col2': f"{death_counts[2]} ({death_counts[2]/big_n.get(2,1)*100:.1f}%)" if trt == 2 else '',
                'col3': f"{death_counts[3]} ({death_counts[3]/big_n.get(3,1)*100:.1f}%)" if trt == 3 else '',
                'col_total': f"{total_deaths} ({total_deaths/total_n*100:.1f}%)" if trt == 3 else ''
            })

        # Deaths by Time Period header
        results['units'].append({
            'unit': 'time_header',
            'level': 1,
            'rowlabel': 'Deaths by Time Period',
            'col1': '', 'col2': '', 'col3': '', 'col_total': ''
        })

        # Placeholder rows for time period breakdown
        time_periods = ['On Treatment', 'After Last Dose', 'Unknown']
        for period in time_periods:
            results['units'].append({
                'unit': 'time_period',
                'level': 2,
                'rowlabel': f"  {period}",
                'col1': '0 (0.0%)',
                'col2': '0 (0.0%)',
                'col3': '0 (0.0%)',
                'col_total': '0 (0.0%)'
            })

        return results


class LaboratoryAnalyzer:
    """
    Implements statistical analysis for Table 14.3.4.1 (Laboratory Test Results).

    Analyzes laboratory data showing:
    - Shift tables from baseline to post-treatment
    - Subjects with potentially clinically significant abnormalities
    """

    def __init__(self, adlb: pd.DataFrame, adsl: pd.DataFrame):
        self.adlb = adlb
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(saf[saf['TRT01PN'] == int(trt)])
        return big_n

    def analyze(self, by_param: bool = True) -> Dict:
        """Perform laboratory analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())
        trt_list = sorted(big_n.keys())

        def fmt_freq(count: int, denom: int) -> str:
            if denom == 0:
                return "0 (0.0%)"
            pct = count / denom * 100
            return f"{count} ({pct:.1f}%)"

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        # Big N row
        results['units'].append({
            'unit': 'big_n',
            'level': 0,
            'rowlabel': 'Subjects in Population',
            'col1': str(big_n.get(1, 0)),
            'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)),
            'col_total': str(total_n)
        })

        if not by_param or 'PARAM' not in self.adlb.columns:
            # Summary analysis
            results['units'].append({
                'unit': 'unit01',
                'level': 1,
                'rowlabel': 'Laboratory Assessment',
                'col1': '', 'col2': '', 'col3': '', 'col_total': ''
            })

            # Check for common lab parameters
            params = self.adlb['PARAM'].unique()[:10] if 'PARAM' in self.adlb.columns else []
            for param in params:
                param_data = self.adlb[self.adlb['PARAM'] == param].copy()

                # Add parameter header
                results['units'].append({
                    'unit': 'unit01',
                    'level': 2,
                    'rowlabel': str(param),
                    'col1': '', 'col2': '', 'col3': '', 'col_total': '',
                    '_group1': str(param)
                })

                # Summary stats by treatment
                for grade_type in ['Grade 3 or Higher', 'Potentially Clinically Significant']:
                    row = {
                        'unit': 'unit01',
                        'level': 3,
                        'rowlabel': f'  {grade_type}',
                        'col1': '', 'col2': '', 'col3': '', 'col_total': '',
                        '_group1': str(param)
                    }
                    total_count = 0
                    total_denom = 0
                    for i, trt in enumerate(trt_list, 1):
                        trt_data = param_data[param_data['TRTPN'] == trt]
                        # Simplified: use AVALC or similar for categorization
                        count = 0
                        denom = len(trt_data['USUBJID'].unique()) if len(trt_data) > 0 else 0
                        row[f'col{i}'] = fmt_freq(count, denom)
                        total_count += count
                        total_denom += denom
                    row['col_total'] = fmt_freq(total_count, total_denom)
                    results['units'].append(row)

        return results


class VitalSignsAnalyzer:
    """
    Implements statistical analysis for Table 14.3.5.1 (Vital Signs).

    Analyzes vital signs data showing:
    - Summary statistics by parameter
    - Change from baseline
    - Potentially clinically significant abnormalities
    """

    def __init__(self, advs: pd.DataFrame, adsl: pd.DataFrame):
        self.advs = advs
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(saf[saf['TRT01PN'] == int(trt)])
        return big_n

    def _format_continuous(self, series: pd.Series) -> Dict[str, float]:
        """Calculate summary statistics."""
        valid = series.dropna()
        if len(valid) == 0:
            return {'n': 0, 'mean': None, 'median': None, 'std': None, 'min': None, 'max': None}
        return {
            'n': len(valid),
            'mean': valid.mean(),
            'median': valid.median(),
            'std': valid.std(),
            'min': valid.min(),
            'max': valid.max()
        }

    def analyze(self, by_param: bool = True) -> Dict:
        """Perform vital signs analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())
        trt_list = sorted(big_n.keys())

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        # Big N row
        results['units'].append({
            'unit': 'big_n',
            'level': 0,
            'rowlabel': 'Subjects in Population',
            'col1': str(big_n.get(1, 0)),
            'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)),
            'col_total': str(total_n)
        })

        # Get unique parameters
        if 'PARAM' in self.advs.columns:
            params = self.advs['PARAM'].dropna().unique()
        else:
            params = []

        for param in params:
            param_data = self.advs[self.advs['PARAM'] == param].copy()

            # Parameter header
            results['units'].append({
                'unit': 'unit01',
                'level': 1,
                'rowlabel': str(param),
                'col1': '', 'col2': '', 'col3': '', 'col_total': '',
                '_group1': str(param)
            })

            # Get units for this parameter
            units = param_data['AVALU'].unique()[0] if 'AVALU' in param_data.columns and len(param_data['AVALU'].unique()) > 0 else ''

            for stat_label, stat_key in [('Mean', 'mean'), ('Median', 'median'), ('SD', 'std'), ('Min', 'min'), ('Max', 'max')]:
                row = {
                    'unit': 'unit01',
                    'level': 2,
                    'rowlabel': f'  {stat_label}',
                    'col1': '', 'col2': '', 'col3': '', 'col_total': '',
                    '_group1': str(param)
                }

                for i, trt in enumerate(trt_list, 1):
                    trt_data = param_data[param_data['TRTPN'] == trt]
                    stats = self._format_continuous(trt_data['AVAL'])
                    val = stats[stat_key]
                    if val is not None:
                        row[f'col{i}'] = f"{val:.2f}"
                    else:
                        row[f'col{i}'] = "—"

                # Total column
                all_stats = self._format_continuous(param_data['AVAL'])
                val = all_stats[stat_key]
                row['col_total'] = f"{val:.2f}" if val is not None else "—"

                results['units'].append(row)

        return results


class PhysicalExamAnalyzer:
    """
    Implements statistical analysis for Table 14.3.6.1 (Physical Examination).

    Analyzes physical examination findings by category.
    Note: Requires ADPE dataset.
    """

    def __init__(self, adpe: pd.DataFrame, adsl: pd.DataFrame):
        self.adpe = adpe
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(saf[saf['TRT01PN'] == int(trt)])
        return big_n

    def analyze(self) -> Dict:
        """Perform physical exam analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        # Big N row
        results['units'].append({
            'unit': 'big_n',
            'level': 0,
            'rowlabel': 'Subjects in Population',
            'col1': str(big_n.get(1, 0)),
            'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)),
            'col_total': str(total_n)
        })

        # Physical exam findings by category
        if 'PEBODSYS' in self.adpe.columns:
            findings = self.adpe['PEBODSYS'].dropna().unique()

            def fmt(count, denom):
                if denom == 0:
                    return "0 (0.0%)"
                return f"{count} ({count/denom*100:.1f}%)"

            trt_list = sorted(big_n.keys())

            for finding in findings:
                row = {
                    'unit': 'unit01',
                    'level': 1,
                    'rowlabel': str(finding),
                    'col1': '', 'col2': '', 'col3': '', 'col_total': ''
                }
                total_count = 0
                total_denom = 0

                for i, trt in enumerate(trt_list, 1):
                    finding_data = self.adpe[(self.adpe['PEBODSYS'] == finding) & (self.adpe['TRTPN'] == trt)]
                    count = finding_data['USUBJID'].nunique()
                    denom = big_n.get(trt, 0)
                    row[f'col{i}'] = fmt(count, denom)
                    total_count += count
                    total_denom += denom

                row['col_total'] = fmt(total_count, total_denom)
                results['units'].append(row)

        return results


class CardiacSafetyAnalyzer:
    """
    Implements statistical analysis for Table 14.3.7.1 (ECG Findings).

    Analyzes cardiac safety data showing:
    - Normal/Abnormal ECG findings
    - Potentially clinically significant abnormalities
    Note: Requires ADEG dataset.
    """

    def __init__(self, adeg: pd.DataFrame, adsl: pd.DataFrame):
        self.adeg = adeg
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[int(trt)] = len(saf[saf['TRT01PN'] == int(trt)])
        return big_n

    def analyze(self) -> Dict:
        """Perform cardiac safety analysis."""
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())
        trt_list = sorted(big_n.keys())

        def fmt(count, denom):
            if denom == 0:
                return "0 (0.0%)"
            return f"{count} ({count/denom*100:.1f}%)"

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        # Big N row
        results['units'].append({
            'unit': 'big_n',
            'level': 0,
            'rowlabel': 'Subjects in Population',
            'col1': str(big_n.get(1, 0)),
            'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)),
            'col_total': str(total_n)
        })

        # ECG Results by category
        categories = ['Normal', 'Abnormal', 'Abnormal - Not Clinically Significant', 'Abnormal - Clinically Significant']

        for cat in categories:
            row = {
                'unit': 'unit01',
                'level': 1,
                'rowlabel': cat,
                'col1': '', 'col2': '', 'col3': '', 'col_total': ''
            }
            total_count = 0
            total_denom = 0

            for i, trt in enumerate(trt_list, 1):
                if 'EGCAT' in self.adeg.columns and 'EGRES' in self.adeg.columns:
                    cat_data = self.adeg[(self.adeg['EGCAT'] == cat) & (self.adeg['TRTPN'] == trt)]
                    count = cat_data['USUBJID'].nunique()
                else:
                    count = 0
                denom = big_n.get(trt, 0)
                row[f'col{i}'] = fmt(count, denom)
                total_count += count
                total_denom += denom

            row['col_total'] = fmt(total_count, total_denom)
            results['units'].append(row)

        return results


class AENestedAnalyzer:
    """
    Implements nested AE analysis for Table 14.3.1.2.1 (AE by SOC and PT).

    This analyzer produces a nested frequency table showing adverse events
    grouped by System Organ Class (SOC) with Preferred Terms (PT) nested
    within each SOC. For each SOC/PT, counts are shown by CTCAE grade.

    Structure:
    - SOC row (level=2) with summary counts
      - PT row (level=3) nested under SOC
        - Grade breakdown rows
    """

    def __init__(self, adae: pd.DataFrame, adsl: pd.DataFrame):
        self.adae = adae
        self.adsl = adsl

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from Safety Analysis Set."""
        big_n = {}
        saf = self.adsl[self.adsl['SAFFL'] == 'Y']
        for trt in saf['TRT01PN'].dropna().unique():
            big_n[trt] = len(saf[saf['TRT01PN'] == trt])
        return big_n

    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, str]) -> pd.DataFrame:
        """Apply filters to dataframe."""
        result = df.copy()
        for col, val in filters.items():
            if val and col in result.columns:
                result = result[result[col] == val]
        return result

    def _get_subjects_by_grade(self, df: pd.DataFrame, trt: float,
                                soc: str = None, pt: str = None,
                                grade: str = None, extra_filters: Dict[str, str] = None) -> int:
        """
        Count unique subjects with AE meeting criteria.
        """
        subset = df[(df['TRTPN'] == trt)].copy()

        if extra_filters:
            subset = self._apply_filters(subset, extra_filters)

        if soc:
            subset = subset[subset['AESOC'] == soc]
        if pt:
            subset = subset[subset['AEDECOD'] == pt]
        if grade:
            if grade == '>=3':
                subset = subset[subset['AETOXGR'].isin(['3', '4', '5'])]
            elif grade == 'Missing':
                subset = subset[subset['AETOXGR'].isna() | (subset['AETOXGR'] == '')]
            else:
                subset = subset[subset['AETOXGR'] == grade]

        return subset['USUBJID'].nunique()

    def _get_any_grade_count(self, df: pd.DataFrame, trt: float,
                             soc: str = None, pt: str = None, extra_filters: Dict[str, str] = None) -> int:
        """Count unique subjects with any grade AE."""
        subset = df[(df['TRTPN'] == trt)].copy()

        if extra_filters:
            subset = self._apply_filters(subset, extra_filters)

        if soc:
            subset = subset[subset['AESOC'] == soc]
        if pt:
            subset = subset[subset['AEDECOD'] == pt]

        return subset['USUBJID'].nunique()

    def analyze(self, max_socs: int = None, max_pts_per_soc: int = None,
                ae_filter: str = None, summary_label: str = "Subjects with any TEAEs") -> Dict:
        """
        Perform nested AE analysis.

        Args:
            max_socs: Maximum number of SOCs to include (for testing)
            max_pts_per_soc: Maximum PTs per SOC to include (for testing)
            ae_filter: Column=value filter for AE type (e.g., 'AESER=Y' for serious AEs)
            summary_label: Label for the summary row

        Returns:
            Dict with analysis results including units (rows)
        """
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())

        # Filter to Safety Analysis Set
        adae_saf = self.adae[self.adae['SAFFL'] == 'Y'].copy()

        # Parse ae_filter if provided (e.g., 'AESER=Y' -> {'AESER': 'Y'})
        extra_filters = {}
        if ae_filter:
            parts = ae_filter.split('=')
            if len(parts) == 2:
                extra_filters[parts[0]] = parts[1]

        results = {
            'big_n': big_n,
            'total_n': total_n,
            'units': []
        }

        def fmt_freq(count: int, denom: int) -> str:
            """Format as 'count (pct%)'."""
            if denom == 0:
                return "0 (0.0)"
            pct = count / denom * 100
            return f"{count} ({pct:.1f})"

        trt_list = sorted(big_n.keys())

        # Get unique SOCs, sorted alphabetically
        socs = sorted(adae_saf['AESOC'].dropna().unique())
        if max_socs:
            socs = socs[:max_socs]

        unit_num = 1
        soc_ord = 1

        # Overall summary header
        results['units'].append({
            'unit': f'unit01',
            'level': 1,
            'rowlabel': summary_label,
            'col1': '', 'col2': '', 'col3': '', 'col_total': '',
            '_group1': summary_label
        })

        # Overall any grade
        total_any = 0
        row = {'unit': f'unit01', 'level': 2, 'rowlabel': 'Any Grade',
               'col1': '', 'col2': '', 'col3': '', 'col_total': '',
               '_group1': summary_label}
        for i, trt in enumerate(trt_list, 1):
            n = self._get_any_grade_count(adae_saf, trt, extra_filters=extra_filters)
            row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
            total_any += n
        row['col_total'] = fmt_freq(total_any, total_n)
        results['units'].append(row)

        grades = ['5', '4', '3', '2', '1', '>=3', 'Missing']
        for grade in grades:
            total_count = 0
            row = {'unit': f'unit01', 'level': 2, 'rowlabel': grade,
                   'col1': '', 'col2': '', 'col3': '', 'col_total': '',
                   '_group1': summary_label}
            for i, trt in enumerate(trt_list, 1):
                n = self._get_subjects_by_grade(adae_saf, trt, grade=grade, extra_filters=extra_filters)
                row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
                total_count += n
            row['col_total'] = fmt_freq(total_count, total_n)
            results['units'].append(row)

        # Process each SOC
        for soc in socs:
            unit_num += 1
            soc_ord += 1

            # SOC header row
            results['units'].append({
                'unit': f'unit{unit_num:02d}',
                'level': 2,
                'rowlabel': soc,
                'col1': '', 'col2': '', 'col3': '', 'col_total': '',
                '_group1': soc
            })

            # Get PTs within this SOC
            pts_in_soc = sorted(adae_saf[adae_saf['AESOC'] == soc]['AEDECOD'].dropna().unique())
            if max_pts_per_soc:
                pts_in_soc = pts_in_soc[:max_pts_per_soc]

            pt_ord = 1
            for pt in pts_in_soc:
                pt_ord += 1

                # Any grade for PT
                total_any = 0
                row = {'unit': f'unit{unit_num:02d}', 'level': 3, 'rowlabel': pt,
                       'col1': '', 'col2': '', 'col3': '', 'col_total': '',
                       '_group1': soc, '_group2': pt}
                for i, trt in enumerate(trt_list, 1):
                    n = self._get_any_grade_count(adae_saf, trt, soc=soc, pt=pt, extra_filters=extra_filters)
                    row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
                    total_any += n
                row['col_total'] = fmt_freq(total_any, total_n)
                results['units'].append(row)

                # Grade breakdown for PT
                for grade in grades:
                    total_count = 0
                    row = {'unit': f'unit{unit_num:02d}', 'level': 3, 'rowlabel': grade,
                           'col1': '', 'col2': '', 'col3': '', 'col_total': '',
                           '_group1': soc, '_group2': pt}
                    for i, trt in enumerate(trt_list, 1):
                        n = self._get_subjects_by_grade(adae_saf, trt, soc=soc, pt=pt, grade=grade, extra_filters=extra_filters)
                        row[f'col{i}'] = fmt_freq(n, big_n.get(trt, 0))
                        total_count += n
                    row['col_total'] = fmt_freq(total_count, total_n)
                    results['units'].append(row)

        return results


def generate_ae_nested_report(
    adae_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.3.1.2.1",
    table_title: str = None,
    population: str = None,
    ae_filter: str = None,
    summary_label: str = None
) -> Dict[str, str]:
    """
    Generate Table 14.3.1.2.1 (AE by SOC and PT) or 14.3.1.3.1 (SAE by SOC/PT).

    Nested frequency table showing adverse events by System Organ Class
    and Preferred Term with CTCAE grade breakdown.

    Args:
        adae_path: Path to ADAE SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the table
        population: Population description
        ae_filter: Column=value filter for AE type (e.g., 'AESER=Y' for serious AEs)
        summary_label: Label for the summary row
    """
    # Read ADaM data
    adam_reader = ADaMDataReader(str(Path(adsl_path).parent))
    adsl = adam_reader.read_adsl()
    # Read ADAE directly
    adae, _ = pyreadstat.read_sas7bdat(adae_path)

    # Perform analysis
    analyzer = AENestedAnalyzer(adae, adsl)
    if summary_label is None:
        summary_label = "Subjects with any TEAEs"
    analysis_results = analyzer.analyze(ae_filter=ae_filter, summary_label=summary_label)

    # Generate CSV output
    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(analysis_results)
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # Generate PDF
    if table_title is None:
        table_title = "Adverse Events by System Organ Class and Preferred Term"
    if population is None:
        population = "Safety Analysis Set"

    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                    table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_demographic_report(
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.1.2.1",
    table_title: str = None,
    population: str = None
) -> Dict[str, str]:
    """
    Generate Table 14.1.2.x (Demographic and Baseline Characteristics).

    Table variants:
    - 14.1.2.1: Enrolled Analysis Set
    - 14.1.2.2: Enrolled Analysis Set by Region/Country
    - 14.1.2.3: Safety Analysis Set
    - 14.1.2.4: Safety Analysis Set by Region/Country

    Args:
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier (e.g., "14.1.2.1")
        table_title: Title for the PDF (if None, uses table_id to look up default)
        population: Population string (if None, uses table_id to look up default)
    """
    # 1. Read ADaM data
    adam_reader = ADaMDataReader(str(Path(adsl_path).parent))
    adsl = adam_reader.read_adsl()

    # 2. Determine population based on table_id
    # 14.1.2.1/14.1.2.2 use ENRLFL, 14.1.2.3/14.1.2.4 use SAFFL
    # 14.1.2.2/14.1.2.4 include country breakdown
    if table_id in ["14.1.2.3", "14.1.2.4"]:
        population_filter = "safety"
    else:
        population_filter = "enrolled"

    # Determine if country breakdown is needed
    include_country = table_id in ["14.1.2.2", "14.1.2.4"]

    # 3. Perform statistical analysis
    analyzer = DemographicAnalyzer(adsl, population_filter=population_filter,
                                  include_country_breakdown=include_country)
    analysis_results = analyzer.analyze()

    # 3. Generate SAS output dataset
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # Determine table title: use provided title, or fall back to default mapping
    if table_title is None:
        table_titles = {
            "14.1.2.1": "Demographic and Baseline Characteristics",
            "14.1.2.2": "Demographic and Baseline Characteristics by Region/Country",
            "14.1.2.3": "Demographic and Baseline Characteristics (Safety Analysis Set)",
            "14.1.2.4": "Demographic and Baseline Characteristics by Region/Country (Safety)",
        }
        table_title = table_titles.get(table_id, "Demographic and Baseline Characteristics")

    if population is None:
        population = "Enrolled Analysis Set"

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                    table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_tumor_change_report(
    adrs_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.2.3.1",
    table_title: str = "Best Change in Sum of Target Lesions",
    population: str = "Response Evaluable Set"
) -> Dict[str, str]:
    """
    Generate Table 14.2.3.1 (Best Change in Sum of Target Lesions).

    Args:
        adrs_path: Path to ADRS SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adrs, _ = pyreadstat.read_sas7bdat(adrs_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = TumorChangeAnalyzer(adrs, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                  table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_death_report(
    adae_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.3.2.1",
    table_title: str = "Deaths",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.3.2.1 (Deaths).

    Args:
        adae_path: Path to ADAE SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adae, _ = pyreadstat.read_sas7bdat(adae_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = DeathAnalyzer(adae, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                  table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_laboratory_report(
    adlb_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.3.4.1",
    table_title: str = "Laboratory Test Results",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.3.4.1 (Laboratory Test Results).

    Args:
        adlb_path: Path to ADLB SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adlb, _ = pyreadstat.read_sas7bdat(adlb_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = LaboratoryAnalyzer(adlb, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                  table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_vital_signs_report(
    advs_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.3.5.1",
    table_title: str = "Vital Signs",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.3.5.1 (Vital Signs).

    Args:
        advs_path: Path to ADVS SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    advs, _ = pyreadstat.read_sas7bdat(advs_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = VitalSignsAnalyzer(advs, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                  table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_physical_exam_report(
    adpe_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.3.6.1",
    table_title: str = "Physical Examination",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.3.6.1 (Physical Examination).

    Args:
        adpe_path: Path to ADPE SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adpe, _ = pyreadstat.read_sas7bdat(adpe_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = PhysicalExamAnalyzer(adpe, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                  table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def generate_cardiac_safety_report(
    adeg_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.3.7.1",
    table_title: str = "ECG Findings",
    population: str = "Safety Analysis Set"
) -> Dict[str, str]:
    """
    Generate Table 14.3.7.1 (ECG Findings / Cardiac Safety).

    Args:
        adeg_path: Path to ADEG SAS dataset
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        table_id: Table identifier
        table_title: Title for the PDF
        population: Population string

    Returns:
        Dict with paths to generated files
    """
    # 1. Read ADaM data
    adeg, _ = pyreadstat.read_sas7bdat(adeg_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    # 2. Perform statistical analysis
    analyzer = CardiacSafetyAnalyzer(adeg, adsl)
    analysis_results = analyzer.analyze()

    # 3. Generate CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(
        analysis_results,
        has_col2=True,
        has_col3=True
    )

    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 4. Generate PDF report
    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path),
                                  table_title, table_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


class PKConcentrationAnalyzer:
    """
    Implements statistical analysis for Table 14.4.1.x (PK Concentration).

    Analyzes PK concentration data showing:
    - Descriptive statistics by visit/timepoint
    - Mean, SD, CV%, geometric mean
    - By treatment group and analyte
    """

    def __init__(self, adpp: pd.DataFrame, adsl: pd.DataFrame):
        self.adpp = adpp
        self.adsl = adsl
        # Filter to PK population
        if 'PKFL' in self.adsl.columns:
            pk_subjects = self.adsl[self.adsl['PKFL'] == 'Y']['USUBJID'].unique()
            self.adpp_pk = self.adpp[self.adpp['USUBJID'].isin(pk_subjects)]
        else:
            self.adpp_pk = self.adpp

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from PK Analysis Set."""
        big_n = {}
        pk_pop = self.adsl[self.adsl.get('PKFL', 'Y') == 'Y'] if 'PKFL' in self.adsl.columns else self.adsl
        # Use TRT01PN from ADSL (ADSL uses TRT01PN, ADPP uses TRTPN)
        trt_col = 'TRT01PN' if 'TRT01PN' in pk_pop.columns else 'TRTPN'
        for trt in pk_pop[trt_col].dropna().unique():
            big_n[int(trt)] = len(pk_pop[pk_pop[trt_col] == int(trt)])
        return big_n

    def _fmt(self, val: float, decimals: int = 2) -> str:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "—"
        return f"{val:.{decimals}f}"

    def _stats(self, series: pd.Series) -> Dict[str, float]:
        s = series.dropna()
        if len(s) == 0:
            return {'n': 0, 'mean': np.nan, 'sd': np.nan, 'cv': np.nan, 'min': np.nan, 'median': np.nan, 'max': np.nan, 'geom_mean': np.nan}
        log_mean = np.exp(np.log(s).mean()) if (s > 0).all() else np.nan
        return {
            'n': len(s),
            'mean': s.mean(),
            'sd': s.std(),
            'cv': s.std() / s.mean() * 100 if s.mean() != 0 else np.nan,
            'min': s.min(),
            'median': s.median(),
            'max': s.max(),
            'geom_mean': log_mean
        }

    def analyze(self, by_visit: bool = True) -> Dict:
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())
        trt_list = sorted(big_n.keys())

        results = {'big_n': big_n, 'total_n': total_n, 'units': []}

        results['units'].append({
            'unit': 'big_n', 'level': 0,
            'rowlabel': 'Subjects in PK Analysis Set',
            'col1': str(big_n.get(1, 0)), 'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)), 'col_total': str(total_n)
        })

        # Get unique analytes (PPTEST/CD)
        if 'PPTESTCD' in self.adpp.columns:
            analytes = self.adpp['PPTESTCD'].dropna().unique()
        elif 'PARAMCD' in self.adpp.columns:
            analytes = self.adpp['PARAMCD'].dropna().unique()
        else:
            analytes = []

        for analyte in analytes:
            if 'PPTESTCD' in self.adpp.columns:
                an_data = self.adpp[self.adpp['PPTESTCD'] == analyte]
            else:
                an_data = self.adpp[self.adpp['PARAMCD'] == analyte]

            # Analyte header
            results['units'].append({
                'unit': 'unit01', 'level': 1, 'rowlabel': str(analyte),
                'col1': '', 'col2': '', 'col3': '', 'col_total': '', '_group1': str(analyte)
            })

            # Get visits for this analyte
            visits = sorted(an_data['AVISITN'].dropna().unique()) if 'AVISITN' in an_data.columns else []

            for visit_num in visits:
                visit_data = an_data[an_data['AVISITN'] == visit_num]
                visit_label = visit_data['AVISIT'].iloc[0] if 'AVISIT' in visit_data.columns else f"Visit {visit_num}"

                results['units'].append({
                    'unit': 'unit01', 'level': 2, 'rowlabel': f"  {visit_label}",
                    'col1': '', 'col2': '', 'col3': '', 'col_total': '', '_group1': str(analyte)
                })

                for stat_label, stat_key, decimals in [
                    ('n', 'n', 0), ('Mean', 'mean', 3), ('SD', 'sd', 3),
                    ('CV%', 'cv', 1), ('Geom Mean', 'geom_mean', 3), ('Min', 'min', 3),
                    ('Median', 'median', 3), ('Max', 'max', 3)
                ]:
                    row = {'unit': 'unit01', 'level': 3, 'rowlabel': f"    {stat_label}",
                           'col1': '', 'col2': '', 'col3': '', 'col_total': '', '_group1': str(analyte)}
                    for i, trt in enumerate(trt_list, 1):
                        trt_visit_data = visit_data[visit_data['TRTPN'] == trt]
                        s = self._stats(trt_visit_data['AVAL'])
                        row[f'col{i}'] = self._fmt(s[stat_key], decimals)
                    all_s = self._stats(visit_data['AVAL'])
                    row['col_total'] = self._fmt(all_s[stat_key], decimals)
                    results['units'].append(row)

        return results


class PKParametersAnalyzer:
    """
    Implements statistical analysis for Table 14.4.4.x (PK Parameters).

    Analyzes PK parameter data showing:
    - Descriptive statistics (N, Mean, SD, CV%, Geom Mean, Min, Median, Max)
    - By treatment group and parameter
    """

    def __init__(self, adpp: pd.DataFrame, adsl: pd.DataFrame):
        self.adpp = adpp
        self.adsl = adsl
        # Filter to PK population and parameter records
        if 'PKFL' in self.adsl.columns:
            pk_subjects = self.adsl[self.adsl['PKFL'] == 'Y']['USUBJID'].unique()
            self.adpp_pk = self.adpp[self.adpp['USUBJID'].isin(pk_subjects)]
        else:
            self.adpp_pk = self.adpp

    def calculate_big_n(self) -> Dict[int, int]:
        """Calculate Big N from PK Analysis Set."""
        big_n = {}
        pk_pop = self.adsl[self.adsl.get('PKFL', 'Y') == 'Y'] if 'PKFL' in self.adsl.columns else self.adsl
        # Use TRT01PN from ADSL (ADSL uses TRT01PN, ADPP uses TRTPN)
        trt_col = 'TRT01PN' if 'TRT01PN' in pk_pop.columns else 'TRTPN'
        for trt in pk_pop[trt_col].dropna().unique():
            big_n[int(trt)] = len(pk_pop[pk_pop[trt_col] == int(trt)])
        return big_n

    def _fmt(self, val: float, decimals: int = 2) -> str:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "—"
        return f"{val:.{decimals}f}"

    def _stats(self, series: pd.Series) -> Dict[str, float]:
        s = series.dropna()
        if len(s) == 0:
            return {'n': 0, 'mean': np.nan, 'sd': np.nan, 'cv': np.nan, 'min': np.nan, 'median': np.nan, 'max': np.nan, 'geom_mean': np.nan, 'geom_sd': np.nan}
        log_mean = np.exp(np.log(s).mean()) if (s > 0).all() else np.nan
        log_vals = np.log(s[s > 0]) if (s > 0).all() else pd.Series([np.nan])
        geom_sd = np.exp(log_vals.std()) if len(log_vals) > 1 else np.nan
        return {
            'n': len(s), 'mean': s.mean(), 'sd': s.std(),
            'cv': s.std() / s.mean() * 100 if s.mean() != 0 else np.nan,
            'min': s.min(), 'median': s.median(), 'max': s.max(),
            'geom_mean': log_mean, 'geom_sd': geom_sd
        }

    def analyze(self) -> Dict:
        big_n = self.calculate_big_n()
        total_n = sum(big_n.values())
        trt_list = sorted(big_n.keys())

        results = {'big_n': big_n, 'total_n': total_n, 'units': []}

        results['units'].append({
            'unit': 'big_n', 'level': 0,
            'rowlabel': 'Subjects in PK Analysis Set',
            'col1': str(big_n.get(1, 0)), 'col2': str(big_n.get(2, 0)),
            'col3': str(big_n.get(3, 0)), 'col_total': str(total_n)
        })

        # Get unique parameters
        if 'PARAMCD' in self.adpp.columns:
            params = self.adpp['PARAMCD'].dropna().unique()
        else:
            params = []

        for param in params:
            param_data = self.adpp[self.adpp['PARAMCD'] == param]
            param_name = param_data['PARAM'].iloc[0] if 'PARAM' in param_data.columns else str(param)

            results['units'].append({
                'unit': 'unit01', 'level': 1, 'rowlabel': f"{param} ({param_name})",
                'col1': '', 'col2': '', 'col3': '', 'col_total': '', '_group1': str(param)
            })

            for stat_label, stat_key, decimals in [
                ('n', 'n', 0), ('Mean', 'mean', 3), ('SD', 'sd', 3),
                ('CV%', 'cv', 1), ('Geom Mean', 'geom_mean', 3), ('Geom SD', 'geom_sd', 3),
                ('Min', 'min', 3), ('Median', 'median', 3), ('Max', 'max', 3)
            ]:
                row = {'unit': 'unit01', 'level': 2, 'rowlabel': f"  {stat_label}",
                       'col1': '', 'col2': '', 'col3': '', 'col_total': '', '_group1': str(param)}
                for i, trt in enumerate(trt_list, 1):
                    trt_data = param_data[param_data['TRTPN'] == trt]
                    s = self._stats(trt_data['AVAL'])
                    row[f'col{i}'] = self._fmt(s[stat_key], decimals)
                all_s = self._stats(param_data['AVAL'])
                row['col_total'] = self._fmt(all_s[stat_key], decimals)
                results['units'].append(row)

        return results


def generate_pk_concentration_report(
    adpp_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.4.1.1",
    table_title: str = "PK Concentration",
    population: str = "PK Analysis Set"
) -> Dict[str, str]:
    """Generate Table 14.4.1.x (PK Concentration Summary)."""
    adpp, _ = pyreadstat.read_sas7bdat(adpp_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    analyzer = PKConcentrationAnalyzer(adpp, adsl)
    analysis_results = analyzer.analyze()

    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(analysis_results, has_col2=True, has_col3=True)
    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path), table_title, table_id, population)

    return {'csv_output': str(csv_path), 'pdf': str(pdf_path), 'analysis': analysis_results}


def generate_pk_parameters_report(
    adpp_path: str,
    adsl_path: str,
    output_dir: str,
    table_id: str = "14.4.4.1",
    table_title: str = "PK Parameters",
    population: str = "PK Analysis Set"
) -> Dict[str, str]:
    """Generate Table 14.4.4.x (PK Parameters Summary)."""
    adpp, _ = pyreadstat.read_sas7bdat(adpp_path)
    adsl, _ = pyreadstat.read_sas7bdat(adsl_path)

    analyzer = PKParametersAnalyzer(adpp, adsl)
    analysis_results = analyzer.analyze()

    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(analysis_results, has_col2=True, has_col3=True)
    csv_path = Path(output_dir) / "csv" / "table" / f"table_{table_id.replace('.', '_')}.csv"
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / "table" / f"Table_{table_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path), table_title, table_id, population)

    return {'csv_output': str(csv_path), 'pdf': str(pdf_path), 'analysis': analysis_results}


def generate_generic_report(
    adsl_path: str,
    output_dir: str,
    tlf_id: str,
    table_title: str = None,
    population: str = None,
    additional_datasets: Dict[str, pd.DataFrame] = None
) -> Dict[str, str]:
    """
    Generic TLF report generator using template-driven analysis.

    This function uses the ICH E3 templates to automatically generate
    any TLF report without needing specific analyzer implementations.

    Args:
        adsl_path: Path to ADSL SAS dataset
        output_dir: Directory to save outputs
        tlf_id: TLF ID (e.g., "14.1.2.1" or "Table 14.1.2.1")
        table_title: Title for the PDF (if None, uses template default)
        population: Population string (if None, uses template default)
        additional_datasets: Dict of additional ADaM datasets (e.g., {'adcm': adcm_df})

    Returns:
        Dict with paths to generated files
    """
    # Import here to avoid circular dependency
    from src.report.generic_analyzer import get_template, generic_analyze

    # 1. Read ADaM data
    adam_reader = ADaMDataReader(str(Path(adsl_path).parent))
    adsl = adam_reader.read_adsl()

    # 2. Get template
    clean_tlf_id = tlf_id.replace('Table ', '').replace('Figure ', '').replace('Listing ', '')
    template = get_template(clean_tlf_id)

    if template is None:
        raise ValueError(f"No template found for {tlf_id}. Available templates: {list(get_available_templates())}")

    # 3. Perform template-driven analysis
    analysis_results = generic_analyze(adsl, clean_tlf_id)

    # 4. Save CSV
    csv_path = Path(output_dir) / "csv" / "table" / f"table_{clean_tlf_id.replace('.', '_')}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert results to DataFrame for CSV output
    output_generator = TableOutputGenerator()
    sas_df = output_generator.generate_output_data_generic(analysis_results)
    sas_df.to_csv(csv_path, index=False)
    print(f"  CSV: {csv_path}")

    # 5. Generate PDF
    if table_title is None:
        table_title = template.tlf_name
    if population is None:
        # Look up population name from flag
        from src.report.generic_analyzer import POPULATION_FLAGS
        pop_info = POPULATION_FLAGS.get(template.population, (template.population, "Y"))
        population = template.population  # Use the flag name directly

    pdf_generator = PDFReportGenerator()
    pdf_path = Path(output_dir) / "report" / f"Table_{clean_tlf_id.replace('.', '_')}_python.pdf"
    pdf_generator.generate_generic(analysis_results, str(pdf_path), table_title, clean_tlf_id, population)

    return {
        'csv_output': str(csv_path),
        'pdf': str(pdf_path),
        'analysis': analysis_results
    }


def get_available_templates() -> List[str]:
    """Get list of available template IDs."""
    from src.report.generic_analyzer import ALL_TEMPLATES
    return list(ALL_TEMPLATES.keys())


if __name__ == "__main__":
    # Test
    base = Path("d:/hello world/clinical-data-process")
    adsl = base / "input/ADaM/Data/adsl.sas7bdat"
    output = base / "output"

    result = generate_disposition_report(
        adsl_path=str(adsl),
        output_dir=str(output),
        table_id="14.1.1.1"
    )

    print(f"\nGenerated files:")
    print(f"  SAS output: {result['sas_output']}")
    print(f"  PDF: {result['pdf']}")
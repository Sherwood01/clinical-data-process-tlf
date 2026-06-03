#!/usr/bin/env python
"""
Quick TLF Generator - Generate Table/Figure/Listing from TOC
Usage:
    python quick_gen.py "Table 14.1.2.1"    # From TOC lookup
    python quick_gen.py "Table 14.1.1.1"
    python quick_gen.py "Listing 16.2.1.1"
    python quick_gen.py "Figure 14.2.1.1"
"""

import sys
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

BASE_DIR = Path("d:/hello world/clinical-data-process")
INPUT_DIR = BASE_DIR / "input/ADaM/Data"
OUTPUT_DIR = BASE_DIR / "output"
REPORT_DIR = OUTPUT_DIR / "report"
SAS_DIR = OUTPUT_DIR / "sas"
CSV_DIR = OUTPUT_DIR / "csv"
TOC_DIR = OUTPUT_DIR / "toc"
TOC_FILE = TOC_DIR / "tlf_toc_full.csv"


def get_table_info_from_toc(tlf_id: str) -> dict:
    """Look up TLF info from TOC CSV."""
    if not TOC_FILE.exists():
        print(f"Error: TOC file not found: {TOC_FILE}")
        print("Please run: python main.py --full-toc first")
        return None

    toc_df = pd.read_csv(TOC_FILE)

    # Find matching entry (tlf_id column contains "Table 14.1.2.1" etc)
    match = toc_df[toc_df['tlf_id'] == tlf_id]
    if match.empty:
        print(f"Error: '{tlf_id}' not found in TOC")
        print(f"\nTOC contains {len(toc_df)} entries. Examples:")
        print(toc_df['tlf_id'].head(10).tolist())
        return None

    row = match.iloc[0]
    return {
        'tlf_id': row['tlf_id'],
        'tlf_name': row['tlf_name'],
        'tlf_type': row['tlf_type'],
        'population': row['population']
    }


def get_analysis_type(tlf_id: str) -> str:
    """Determine analysis type from TLF ID section."""
    # Extract the full ID without prefix
    clean_id = tlf_id.replace('Table ', '').replace('Figure ', '').replace('Listing ', '')
    parts = clean_id.split('.')

    # For 14.1.1.x sub-sections
    if len(parts) >= 4 and parts[0] == '14' and parts[1] == '1' and parts[2] == '1':
        sub_num = parts[3]
        if sub_num == '1':
            return "disposition"
        elif sub_num == '2':
            return "protocol_deviation"
        elif sub_num == '3':
            return "exclusion"

    # For 14.3.1.2.x - AE by SOC/PT (nested table)
    if len(parts) >= 4 and parts[0] == '14' and parts[1] == '3' and parts[2] == '1' and parts[3] == '2':
        return "ae_nested"

    # For 14.3.1.3.x - AE by severity (another nested type)
    if len(parts) >= 4 and parts[0] == '14' and parts[1] == '3' and parts[2] == '1' and parts[3] == '3':
        return "ae_nested"

    # For 14.3.1.4.x - Related AE by SOC/PT (nested table)
    if len(parts) >= 4 and parts[0] == '14' and parts[1] == '3' and parts[2] == '1' and parts[3] == '4':
        return "ae_nested"

    # Extract section number like "14.1.2" for other tables
    section = '.'.join(parts[:3])

    # Map section to analysis type
    section_to_type = {
        "14.1.1": "disposition",
        "14.1.2": "demographics",
        "14.1.3": "medical_history",
        "14.1.4": "medications",
        "14.1.5": "exposure",
        "14.2.1": "response",
        "14.2.2": "survival",
        "14.2.3": "tumor_change",
        "14.2.4": "disease_control",
        "14.2.5": "subgroup",
        "14.3.1": "ae_summary",
        "14.3.2": "death",
        "14.3.3": "narratives",
        "14.3.4": "laboratory",
        "14.3.5": "vital_signs",
        "14.3.6": "physical_exam",
        "14.3.7": "cardiac_safety",
        "14.4.1": "pk_concentration",
        "14.4.2": "pk_concentration",
        "14.4.3": "pk_concentration",
        "14.4.4": "pk_parameters",
        "14.4.7": "immunogenicity",
        "14.4.8": "biomarkers",
    }

    return section_to_type.get(section, "unknown")


def get_required_datasets(tlf_id: str) -> list:
    """Determine required ADaM datasets from TLF ID."""
    section = '.'.join(tlf_id.replace('Table ', '').replace('Figure ', '').replace('Listing ', '').split('.')[:3])

    # Datasets needed by section
    section_datasets = {
        "14.1.1": ["adsl"],
        "14.1.2": ["adsl"],
        "14.1.3": ["adsl", "admh"],
        "14.1.4": ["adsl", "adcm"],
        "14.1.5": ["adsl", "adex"],
        "14.2.1": ["adsl", "adrs"],
        "14.2.2": ["adsl", "adtte"],
        "14.2.3": ["adsl", "adrs"],
        "14.2.4": ["adsl", "adrs"],
        "14.2.5": ["adsl", "adrs"],
        "14.3.1": ["adsl", "adae"],
        "14.3.2": ["adsl", "adae"],
        "14.3.3": ["adsl"],
        "14.3.4": ["adsl"],
        "14.3.5": ["adsl"],
        "14.3.6": ["adsl"],
        "14.3.7": ["adsl"],
        "14.4.1": ["adsl", "adpp"],
        "14.4.2": ["adsl", "adpp"],
        "14.4.3": ["adsl", "adpp"],
        "14.4.4": ["adsl", "adpp"],
        "14.4.7": ["adsl", "adab"],
        "14.4.8": ["adsl"],
    }

    return section_datasets.get(section, ["adsl"])


def generate_figure(tlf_id: str, clean_id: str, info: dict):
    """Generate a Figure (KM plot, Waterfall, Swimmer, Spider)."""
    import pyreadstat
    import matplotlib.pyplot as plt
    from pathlib import Path
    from src.report.figure_generator import FigureGenerator

    print(f"\n[Generating Figure...]")

    # Determine figure type from ID
    section = '.'.join(clean_id.split('.')[:3])

    try:
        fig_gen = FigureGenerator()
        output_path = OUTPUT_DIR / "report" / "figure" / f"Figure_{clean_id.replace('.', '_')}.pdf"

        if section == "14.2.1":
            # Overall Survival KM - filter ADTTE for OS
            adsl, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adsl.sas7bdat"))
            adtte, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adtte.sas7bdat"))

            # Filter for OS data and merge with adsl for treatment
            os_data = adtte[adtte['PARAM'] == 'Overall Survival (days)'].copy()
            os_data = os_data.merge(adsl[['USUBJID', 'TRT01PN']], on='USUBJID', how='left')

            result = fig_gen.generate_km_plot(
                adttte=os_data,
                table_id=clean_id,
                figure_title=info['tlf_name'],
                population=info['population'],
                param_filter="Overall Survival",
                treatment_col="TRT01PN",
                output_path=str(output_path)
            )
            print(f"  Figure: {output_path}")
            return {'pdf': str(output_path)}

        elif section == "14.2.2":
            # PFS KM
            adsl, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adsl.sas7bdat"))
            adtte, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adtte.sas7bdat"))

            pfs_data = adtte[adtte['PARAM'] == 'Progression Free Survival (days)'].copy()
            pfs_data = pfs_data.merge(adsl[['USUBJID', 'TRT01PN']], on='USUBJID', how='left')

            result = fig_gen.generate_km_plot(
                adttte=pfs_data,
                table_id=clean_id,
                figure_title=info['tlf_name'],
                population=info['population'],
                param_filter="Progression Free Survival",
                treatment_col="TRT01PN",
                output_path=str(output_path)
            )
            print(f"  Figure: {output_path}")
            return {'pdf': str(output_path)}

        elif section == "14.2.3":
            # Forest Plot for ORR
            adrs, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adrs.sas7bdat"))
            adsl, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adsl.sas7bdat"))
            from src.report.figure_generator import ResponseFigureGenerator
            resp_gen = ResponseFigureGenerator()
            result = resp_gen.generate_forest_plot(
                adrs=adrs,
                adsl=adsl,
                table_id=clean_id,
                figure_title=info['tlf_name'],
                population=info['population'],
                output_path=str(output_path)
            )
            print(f"  Figure: {output_path}")
            return {'pdf': str(output_path)}

        elif section == "14.2.4":
            # Waterfall, Swimmer, or Spider
            adrs, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adrs.sas7bdat"))
            adsl, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adsl.sas7bdat"))
            adtte, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adtte.sas7bdat"))

            name_lower = info['tlf_name'].lower()

            if "waterfall" in name_lower or "best" in name_lower:
                result = fig_gen.generate_waterfall_plot(
                    adrs=adrs,
                    table_id=clean_id,
                    figure_title=info['tlf_name'],
                    population=info['population'],
                    treatment_col="TRTPN",
                    output_path=str(output_path)
                )
            elif "spider" in name_lower:
                # Spider plot - fallback to swimmer if no tumor change data
                has_tumor_change = any(c in adrs.columns for c in ['NRTRN', 'CHG', 'TUMCAL'])
                if has_tumor_change:
                    result = fig_gen.generate_spider_plot(
                        adrs=adrs,
                        table_id=clean_id,
                        figure_title=info['tlf_name'],
                        population=info['population'],
                        treatment_col="TRTPN",
                        output_path=str(output_path)
                    )
                else:
                    # Fallback to swimmer for now
                    result = fig_gen.generate_swimmer_plot(
                        adsl=adrs,
                        table_id=clean_id,
                        figure_title=info['tlf_name'] + " (Swimmer View)",
                        population=info['population'],
                        treatment_col="TRTPN",
                        output_path=str(output_path)
                    )
            elif "swimmer" in name_lower:
                result = fig_gen.generate_swimmer_plot(
                    adsl=adsl,
                    adtte=adtte,
                    table_id=clean_id,
                    figure_title=info['tlf_name'],
                    population=info['population'],
                    treatment_col="TRT01PN",
                    output_path=str(output_path)
                )
            else:
                # Default to swimmer
                result = fig_gen.generate_swimmer_plot(
                    adsl=adsl,
                    adtte=adtte,
                    table_id=clean_id,
                    figure_title=info['tlf_name'],
                    population=info['population'],
                    treatment_col="TRT01PN",
                    output_path=str(output_path)
                )
            print(f"  Figure: {output_path}")
            return {'pdf': str(output_path)}

        elif section == "14.3.3":
            # Lab figures - box plot or line plot
            adlb, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adlb.sas7bdat"))
            adsl, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adsl.sas7bdat"))

            name_lower = info['tlf_name'].lower()
            if "box" in name_lower or "whisker" in name_lower:
                result = fig_gen.generate_box_plot(
                    adlb=adlb,
                    table_id=clean_id,
                    figure_title=info['tlf_name'],
                    population=info['population'],
                    treatment_col="TRTPN",
                    output_path=str(output_path)
                )
            elif "line" in name_lower:
                # Use first available parameter
                param = adlb['PARAMCD'].iloc[0]
                result = fig_gen.generate_spider_plot(
                    adrs=adlb,  # Reuse spider logic for line plots
                    table_id=clean_id,
                    figure_title=info['tlf_name'],
                    population=info['population'],
                    treatment_col="TRTPN",
                    output_path=str(output_path)
                )
            else:
                print(f"\nWarning: Lab figure type not recognized for {tlf_id}")
                return None

            print(f"  Figure: {output_path}")
            return {'pdf': str(output_path)}

        elif section == "14.3.4":
            # eDISH plot for liver safety
            adlb, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adlb.sas7bdat"))
            output_path = OUTPUT_DIR / "report" / "figure" / f"Figure_{clean_id.replace('.', '_')}.pdf"

            # Get ALT/AST data (max ratio to ULN per subject)
            altast = adlb[adlb['PARAMCD'].isin(['ALT', 'AST'])][['USUBJID', 'TRTPN', 'AVAL', 'ANRHI']].copy()
            altast['RATIO'] = altast['AVAL'] / altast['ANRHI']
            alt_max = altast.groupby('USUBJID')['RATIO'].max().reset_index()
            alt_max.columns = ['USUBJID', 'MAX_ALT_AST']

            # Get Bilirubin data
            bili = adlb[adlb['PARAMCD'] == 'BILI'][['USUBJID', 'AVAL', 'ANRHI']].copy()
            bili['RATIO'] = bili['AVAL'] / bili['ANRHI']
            bili_max = bili.groupby('USUBJID')['RATIO'].max().reset_index()
            bili_max.columns = ['USUBJID', 'MAX_BILI']

            # Merge for eDISH
            edish_data = alt_max.merge(bili_max, on='USUBJID', how='outer')

            fig, ax = plt.subplots(figsize=(6, 5))
            ax.scatter(edish_data['MAX_ALT_AST'], edish_data['MAX_BILI'],
                      c='blue', alpha=0.5, s=30)

            # Reference lines at 3x ALT/AST and 2x BILI (Hy's Law criteria)
            ax.axhline(y=2, color='red', linestyle='--', linewidth=1)
            ax.axvline(x=3, color='red', linestyle='--', linewidth=1)

            ax.set_xlabel("Maximum ALT/AST (× ULN)", fontsize=9)
            ax.set_ylabel("Maximum Total Bilirubin (× ULN)", fontsize=9)
            ax.set_xlim(-0.5, None)
            ax.set_ylim(-0.5, None)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            ax.text(0.98, 0.02, 'Hepatotoxicity Concern Zone', transform=ax.transAxes,
                   fontsize=7, ha='right', va='bottom', color='red', style='italic')

            fig.text(0.5, 0.97, f"Figure {clean_id}", fontsize=10, ha='center', fontweight='normal')
            fig.text(0.5, 0.93, info['tlf_name'], fontsize=9, ha='center')
            fig.text(0.5, 0.89, f"({info['population']})", fontsize=8, ha='center', style='italic')

            plt.tight_layout(rect=[0, 0.05, 1, 0.93])
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(str(output_path), dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()

            print(f"  Figure: {output_path}")
            return {'pdf': str(output_path)}

        elif section.startswith("14.4"):
            # PK concentration plots
            adpp, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adpp.sas7bdat"))
            adsl, _ = pyreadstat.read_sas7bdat(str(INPUT_DIR / "adsl.sas7bdat"))

            # For PK, use swimmer plot style but with concentration over time
            result = fig_gen.generate_swimmer_plot(
                adsl=adpp,  # Use adpp as primary data
                table_id=clean_id,
                figure_title=info['tlf_name'],
                population=info['population'],
                treatment_col="TRTPN",
                output_path=str(output_path)
            )
            print(f"  Figure: {output_path}")
            return {'pdf': str(output_path)}

        else:
            print(f"\nError: Figure generation not yet supported for {tlf_id}")
            return None

    except Exception as e:
        print(f"\nError during figure generation: {e}")
        import traceback
        traceback.print_exc()
        return None


GENERATOR_MAP = {
    "disposition": ("generate_disposition_report", ["adsl"]),
    "demographics": ("generate_demographic_report", ["adsl"]),
    "protocol_deviation": ("generate_protocol_deviation_report", ["adsl", "addv"]),
    "exclusion": ("generate_exclusion_report", ["adsl"]),
    "medical_history": ("generate_medical_history_report", ["adsl", "admh"]),
    "medications": ("generate_prior_medication_report", ["adsl", "adcm"]),
    "concomitant_medications": ("generate_concomitant_medication_report", ["adsl", "adcm"]),
    "exposure": ("generate_exposure_report", ["adsl", "adex"]),
    "response": ("generate_best_overall_response_report", ["adsl", "adrs"]),
    "survival": ("generate_pfs_report", ["adsl", "adtte"]),
    "ae_summary": ("generate_ae_summary_report", ["adsl", "adae"]),
    "ae_nested": ("generate_ae_nested_report", ["adsl", "adae"]),
    "tumor_change": ("generate_tumor_change_report", ["adsl", "adrs"]),
    "death": ("generate_death_report", ["adsl", "adae"]),
    "laboratory": ("generate_laboratory_report", ["adsl", "adlb"]),
    "vital_signs": ("generate_vital_signs_report", ["adsl", "advs"]),
    "physical_exam": ("generate_physical_exam_report", ["adsl", "adpe"]),
    "cardiac_safety": ("generate_cardiac_safety_report", ["adsl", "adeg"]),
    "pk_concentration": ("generate_pk_concentration_report", ["adsl", "adpp"]),
    "pk_parameters": ("generate_pk_parameters_report", ["adsl", "adpp"]),
}


def generate_from_toc(tlf_id: str):
    """Generate TLF by looking up info from TOC."""
    print(f"\n{'='*70}")
    print(f"Generating: {tlf_id}")
    print(f"{'='*70}")

    # Step 1: Get table info from TOC
    info = get_table_info_from_toc(tlf_id)
    if not info:
        return None

    print(f"\n[TOC Lookup]")
    print(f"  Name: {info['tlf_name']}")
    print(f"  Type: {info['tlf_type']}")
    print(f"  Population: {info['population']}")

    # Check if it's a Figure
    tlf_type = info['tlf_type']
    clean_id = tlf_id.replace('Table ', '').replace('Figure ', '').replace('Listing ', '')

    # Handle Figure generation separately
    if tlf_type == 'Figure':
        return generate_figure(tlf_id, clean_id, info)

    # Handle Listing generation
    if tlf_type == 'Listing':
        from src.report.listing_generator import generate_listing_report
        listing_section = '.'.join(clean_id.split('.')[:3])
        print(f"\n[Generating Listing...]")
        print(f"  Listing ID: {clean_id}")
        print(f"  Section: {listing_section}")
        try:
            outputs = generate_listing_report(
                listing_id=clean_id,
                data_dir=str(INPUT_DIR),
                output_dir=str(OUTPUT_DIR)
            )
            print(f"\n{'='*70}")
            print("SUCCESS!")
            print(f"{'='*70}")
            for fmt, path in outputs.items():
                print(f"  {fmt.upper()}: {path}")
            return outputs
        except Exception as e:
            print(f"\nError during listing generation: {e}")
            import traceback
            traceback.print_exc()
            return None

    # Step 2: Determine analysis type and required datasets
    analysis_type = get_analysis_type(tlf_id)
    required_datasets = get_required_datasets(tlf_id)

    print(f"\n[Analysis Configuration]")
    print(f"  Analysis Type: {analysis_type}")
    print(f"  Required Datasets: {required_datasets}")

    # Step 4: Import and call generator
    print(f"\n[Generating...]")

    try:
        from src.report.direct_generator import (
            generate_disposition_report,
            generate_demographic_report,
            generate_protocol_deviation_report,
            generate_exclusion_report,
            generate_medical_history_report,
            generate_prior_medication_report,
            generate_concomitant_medication_report,
            generate_exposure_report,
            generate_best_overall_response_report,
            generate_ae_summary_report,
            generate_ae_nested_report,
            generate_pfs_report,
            generate_tumor_change_report,
            generate_death_report,
            generate_laboratory_report,
            generate_vital_signs_report,
            generate_physical_exam_report,
            generate_cardiac_safety_report,
            generate_pk_concentration_report,
            generate_pk_parameters_report,
            generate_generic_report,
            get_available_templates
        )

        # Build kwargs based on analysis type
        kwargs = {
            "output_dir": str(OUTPUT_DIR),
            "table_title": info['tlf_name'],
            "population": info['population']
        }

        # Route to appropriate generator based on analysis type and table_id
        generated = False

        # Disposition (14.1.1.1)
        if analysis_type == "disposition" and clean_id == "14.1.1.1":
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_disposition_report(**kwargs)
            generated = True

        # Demographics (14.1.2.x)
        elif analysis_type == "demographics" and clean_id.startswith("14.1.2"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_demographic_report(**kwargs)
            generated = True

        # Protocol Deviation (14.1.1.2)
        elif analysis_type == "protocol_deviation" and clean_id == "14.1.1.2":
            kwargs["addv_path"] = str(INPUT_DIR / "addv.sas7bdat")
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_protocol_deviation_report(**kwargs)
            generated = True

        # Exclusion (14.1.1.3)
        elif analysis_type == "exclusion" and clean_id == "14.1.1.3":
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_exclusion_report(**kwargs)
            generated = True

        # Medical History (14.1.3.x)
        elif analysis_type == "medical_history" and clean_id.startswith("14.1.3"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_medical_history_report(**kwargs)
            generated = True

        # Prior Medications (14.1.4.1)
        elif analysis_type == "medications" and clean_id == "14.1.4.1":
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adcm_path"] = str(INPUT_DIR / "adcm.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_prior_medication_report(**kwargs)
            generated = True

        # Concomitant Medications (14.1.4.2)
        elif analysis_type == "medications" and clean_id == "14.1.4.2":
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adcm_path"] = str(INPUT_DIR / "adcm.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_concomitant_medication_report(**kwargs)
            generated = True

        # Exposure (14.1.5.1)
        elif analysis_type == "exposure" and clean_id == "14.1.5.1":
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adex_path"] = str(INPUT_DIR / "adex.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_exposure_report(**kwargs)
            generated = True

        # Best Overall Response (14.2.1.x)
        elif analysis_type == "response" and clean_id.startswith("14.2.1"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adrs_path"] = str(INPUT_DIR / "adrs.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_best_overall_response_report(**kwargs)
            generated = True

        # AE by SOC/PT (14.3.1.2.x) - Nested AE table
        elif analysis_type == "ae_nested" and clean_id.startswith("14.3.1.2"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adae_path"] = str(INPUT_DIR / "adae.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_ae_nested_report(**kwargs)
            generated = True

        # AE by Severity (14.3.1.3.x) - Serious TEAEs nested by SOC/PT
        elif analysis_type == "ae_nested" and clean_id.startswith("14.3.1.3"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adae_path"] = str(INPUT_DIR / "adae.sas7bdat")
            kwargs["table_id"] = clean_id
            kwargs["ae_filter"] = "AESER=Y"
            kwargs["summary_label"] = "Subjects with any Serious TEAEs"
            result = generate_ae_nested_report(**kwargs)
            generated = True

        # Related AE by SOC/PT (14.3.1.4.x) - Treatment-Related TEAEs nested by SOC/PT
        elif analysis_type == "ae_nested" and clean_id.startswith("14.3.1.4"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adae_path"] = str(INPUT_DIR / "adae.sas7bdat")
            kwargs["table_id"] = clean_id
            kwargs["ae_filter"] = "AEREL=RELATED"
            kwargs["summary_label"] = "Subjects with any Treatment-Related AEs"
            result = generate_ae_nested_report(**kwargs)
            generated = True

        # AE Summary (14.3.1.x)
        elif analysis_type == "ae_summary" and clean_id.startswith("14.3.1"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adae_path"] = str(INPUT_DIR / "adae.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_ae_summary_report(**kwargs)
            generated = True

        # Survival/PFS (14.2.2.x)
        elif analysis_type == "survival" and clean_id.startswith("14.2.2"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adtte_path"] = str(INPUT_DIR / "adtte.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_pfs_report(**kwargs)
            generated = True

        # Tumor Change (14.2.3.x)
        elif analysis_type == "tumor_change" and clean_id.startswith("14.2.3"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adrs_path"] = str(INPUT_DIR / "adrs.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_tumor_change_report(**kwargs)
            generated = True

        # Deaths (14.3.2.x)
        elif analysis_type == "death" and clean_id.startswith("14.3.2"):
            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["adae_path"] = str(INPUT_DIR / "adae.sas7bdat")
            kwargs["table_id"] = clean_id
            result = generate_death_report(**kwargs)
            generated = True

        # Laboratory (14.3.4.x) - requires ADLB dataset
        elif analysis_type == "laboratory" and clean_id.startswith("14.3.4"):
            adlb_path = INPUT_DIR / "adlb.sas7bdat"
            if adlb_path.exists():
                kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
                kwargs["adlb_path"] = str(adlb_path)
                kwargs["table_id"] = clean_id
                result = generate_laboratory_report(**kwargs)
                generated = True
            else:
                print(f"\nWarning: ADLB dataset not found at {adlb_path}")
                print("  Laboratory analysis requires adlb.sas7bdat file")
                return None

        # Vital Signs (14.3.5.x) - requires ADVS dataset
        elif analysis_type == "vital_signs" and clean_id.startswith("14.3.5"):
            advs_path = INPUT_DIR / "advs.sas7bdat"
            if advs_path.exists():
                kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
                kwargs["advs_path"] = str(advs_path)
                kwargs["table_id"] = clean_id
                result = generate_vital_signs_report(**kwargs)
                generated = True
            else:
                print(f"\nWarning: ADVS dataset not found at {advs_path}")
                print("  Vital Signs analysis requires advs.sas7bdat file")
                return None

        # Physical Exam (14.3.6.x) - requires ADPE dataset
        elif analysis_type == "physical_exam" and clean_id.startswith("14.3.6"):
            adpe_path = INPUT_DIR / "adpe.sas7bdat"
            if adpe_path.exists():
                kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
                kwargs["adpe_path"] = str(adpe_path)
                kwargs["table_id"] = clean_id
                result = generate_physical_exam_report(**kwargs)
                generated = True
            else:
                print(f"\nWarning: ADPE dataset not found at {adpe_path}")
                print("  Physical Exam analysis requires adpe.sas7bdat file")
                return None

        # Cardiac Safety (14.3.7.x) - requires ADEG dataset
        elif analysis_type == "cardiac_safety" and clean_id.startswith("14.3.7"):
            adeg_path = INPUT_DIR / "adeg.sas7bdat"
            if adeg_path.exists():
                kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
                kwargs["adeg_path"] = str(adeg_path)
                kwargs["table_id"] = clean_id
                result = generate_cardiac_safety_report(**kwargs)
                generated = True
            else:
                print(f"\nWarning: ADEG dataset not found at {adeg_path}")
                print("  Cardiac Safety analysis requires adeg.sas7bdat file")
                return None

        # PK Concentration (14.4.1.x, 14.4.2.x, 14.4.3.x) - requires ADPP dataset
        elif analysis_type == "pk_concentration" and clean_id.startswith(("14.4.1", "14.4.2", "14.4.3")):
            adpp_path = INPUT_DIR / "adpp.sas7bdat"
            if adpp_path.exists():
                kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
                kwargs["adpp_path"] = str(adpp_path)
                kwargs["table_id"] = clean_id
                result = generate_pk_concentration_report(**kwargs)
                generated = True
            else:
                print(f"\nWarning: ADPP dataset not found at {adpp_path}")
                print("  PK analysis requires adpp.sas7bdat file")
                return None

        # PK Parameters (14.4.4.x) - requires ADPP dataset
        elif analysis_type == "pk_parameters" and clean_id.startswith("14.4.4"):
            adpp_path = INPUT_DIR / "adpp.sas7bdat"
            if adpp_path.exists():
                kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
                kwargs["adpp_path"] = str(adpp_path)
                kwargs["table_id"] = clean_id
                result = generate_pk_parameters_report(**kwargs)
                generated = True
            else:
                print(f"\nWarning: ADPP dataset not found at {adpp_path}")
                print("  PK analysis requires adpp.sas7bdat file")
                return None

        # Generic generator fallback
        if not generated:
            # Check if template exists
            available = get_available_templates()
            if clean_id not in available:
                print(f"\nError: No generator or template available for {tlf_id}")
                print(f"  Analysis type: {analysis_type}")
                print(f"  Available templates: {', '.join(sorted(available))[:500]}...")
                print(f"\nTo add support, implement a generator or template in generic_analyzer.py")
                return None

            kwargs["adsl_path"] = str(INPUT_DIR / "adsl.sas7bdat")
            kwargs["tlf_id"] = clean_id
            result = generate_generic_report(**kwargs)

        # Step 5: Show results
        print(f"\n{'='*70}")
        print("SUCCESS!")
        print(f"{'='*70}")
        print(f"  PDF: {result.get('pdf', 'N/A')}")
        if 'csv_output' in result:
            print(f"  CSV: {result['csv_output']}")
        if 'sas_output' in result:
            print(f"  SAS Output: {result['sas_output']}")

        return result

    except Exception as e:
        print(f"\nError during generation: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExample usage:")
        print('  python quick_gen.py "Table 14.1.2.1"')
        print('  python quick_gen.py "Table 14.1.1.1"')
        print('  python quick_gen.py "Listing 16.2.1.1"')
        return

    tlf_id = sys.argv[1]
    generate_from_toc(tlf_id)


if __name__ == "__main__":
    main()

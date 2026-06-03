"""
ICH E3 Guideline based TLF Knowledge Base.
Defines the standard structure for Table, Figure, and Listing IDs in clinical study reports.
"""

from typing import Dict, List, Optional, Tuple

# ICH E3 Section 14 TLF Structure
# Format: (TLF_ID_Pattern, Description, Population_Type)
# Second number: 1=Demographic, 2=Efficacy, 3=Safety, 4=PK

TLF_TEMPLATES = {
    # Section 14.1 - Demographic Data
    "14.1.1": {
        "name": "Subject Disposition",
        "sub_items": {
            "1": "Subject Disposition",
            "2": "Major Protocol Deviations",
            "3": "Subjects Excluded from Analysis Sets",
        }
    },
    "14.1.2": {
        "name": "Demographic and Baseline Characteristics",
        "sub_items": {
            "1": "Demographic and Baseline Characteristics",
            "2": "Demographic and Baseline Characteristics by Region/Country",
            "3": "Demographic and Baseline Characteristics (Safety Analysis Set)",
            "4": "Demographic and Baseline Characteristics by Region/Country (Safety)",
        }
    },
    "14.1.3": {
        "name": "Medical History / Prior Disease",
        "sub_items": {
            "1": "Primary Breast Cancer History",
            "2": "Prior Cancer Systemic Therapy",
            "3": "Medical History",
        }
    },
    "14.1.4": {
        "name": "Prior/Concomitant Medications",
        "sub_items": {
            "1": "Prior Medications by ATC Class and Preferred Term",
            "2": "Concomitant Medications by ATC Class and Preferred Term",
        }
    },
    "14.1.5": {
        "name": "Study Drug Exposure",
        "sub_items": {
            "1": "Study Drug Exposure",
        }
    },

    # Section 14.2 - Efficacy Data
    "14.2.1": {
        "name": "Best Overall Response",
        "sub_items": {
            "1": "Best Overall Response and ORR by Independent Central Review",
            "2": "Best Overall Response and ORR by Investigator Assessment",
            "3": "Sensitivity Analyses of ORR (Response Evaluable Set)",
            "4": "Concordance of BOR between ICR and Investigator",
        }
    },
    "14.2.2": {
        "name": "Duration of Response / Survival",
        "sub_items": {
            "1": "Duration of Response, Duration of Stable Disease, and Time to Response",
            "2": "Progression-Free Survival (PFS)",
            "3": "Overall Survival (OS)",
        }
    },
    "14.2.3": {
        "name": "Tumor Response - Change from Baseline",
        "sub_items": {
            "1": "Change from Baseline in Sum of Diameters by ICR",
            "2": "Change from Baseline in Sum of Diameters by Investigator",
        }
    },
    "14.2.4": {
        "name": "Disease Control Rate",
        "sub_items": {
            "1": "Disease Control Rate (DCR) and Clinical Benefit Rate (CBR)",
        }
    },
    "14.2.5": {
        "name": "Subgroup Analyses",
        "sub_items": {
            "1": "Subgroup Analysis of Duration of Response",
        }
    },

    # Section 14.3 - Safety Data
    "14.3.1": {
        "name": "Treatment-Emergent Adverse Events (TEAE)",
        "sub_items": {
            "1": "Overall Summary of TEAE",
            "2.1": "TEAE by SOC, PT and Worst CTCAE Grade",
            "2.2": "TEAE by Grouped PT and Worst CTCAE Grade",
            "2.3": "TEAE by PT",
            "3.1": "Treatment-emergent SAEs by SOC, PT and Worst CTCAE Grade",
            "3.2": "Treatment-emergent SAEs by PT",
            "4.1": "Treatment-Related AEs by SOC, PT and Worst CTCAE Grade",
            "4.2": "Treatment-Related TEAEs Associated with Study Treatment Discontinuation",
            "5.1": "Recurrent TEAE by Selected PT",
            "5.2": "Subgroup Analysis of TEAE by SOC and PT",
            "5.3": "TEAE by Selected PT and Cycle",
            "6.1": "Treatment-Emergent AESI by Category, PT and Worst CTCAE Grade",
            "6.2": "Treatment-Emergent Serious AESI by Category, PT and Worst CTCAE Grade",
            "7.1": "Time to First TEAE of Special Interest",
            "7.2": "Duration of First TEAE of Special Interest",
            "8.1": "Interstitial Lung Disease Events by CTC Grade (Investigator)",
            "8.2": "Interstitial Lung Disease Events by CTC Grade (ILDAC)",
            "8.3": "Shift Table for ILD Events",
        }
    },
    "14.3.2": {
        "name": "Deaths and Other Serious Adverse Events",
        "sub_items": {
            "1": "Death by Primary Cause and Preferred Term",
            "2.1": "TEAEs Associated with Study Treatment Discontinuation",
            "2.2": "Treatment-Related TEAEs Associated with Discontinuation",
            "3.1": "TEAEs Associated with Dose Reduction",
            "3.2": "Treatment-Related TEAEs Associated with Dose Reduction",
            "4.1": "TEAEs Associated with Drug Interruption",
            "4.2": "Treatment-Related TEAEs Associated with Drug Interruption",
        }
    },
    "14.3.3": {
        "name": "Narratives",
        "sub_items": {}
    },
    "14.3.4": {
        "name": "Laboratory Values",
        "sub_items": {
            "1": "Summary of Results and Change from Baseline in Lab Tests - Hematology",
            "2": "Summary of Results and Change from Baseline in Lab Tests - Blood Chemistry",
            "3": "Summary of Results and Change from Baseline in Lab Tests - Coagulation",
            "4": "Summary of Categorical Results in Lab Tests - Urinalysis",
            "5": "Shift Table of CTCAE Grade in Lab Tests - Hematology",
            "6": "Shift Table of CTCAE Grade in Lab Tests - Blood Chemistry",
            "7": "Liver Chemistry Abnormalities",
        }
    },
    "14.3.5": {
        "name": "Vital Signs and ECG",
        "sub_items": {
            "1": "Summary of Vital Signs and Change from Baseline",
            "2": "Summary of 12-Lead ECG and Change from Baseline",
            "3": "Shift Table of 12-Lead ECG Evaluation from Baseline to Worst",
            "4": "Notable ECG Values",
        }
    },
    "14.3.6": {
        "name": "Physical Examination",
        "sub_items": {
            "1": "Shift Table of Physical Exam from Baseline to Worst On-Treatment",
            "2": "Shift Table of ECOG Performance Scores from Baseline to Worst",
        }
    },
    "14.3.7": {
        "name": "Cardiac Safety / Imaging",
        "sub_items": {
            "1": "Shift Table of ECHO/MUGA Findings from Baseline to Worst",
            "2": "Summary of LVEF (%) and Change from Baseline",
            "3": "Shift Table of LVEF (%) CTCAE Grade from Baseline to Worst",
            "4": "Shift Table of Troponin Findings from Baseline to Worst",
            "5": "Relationship between Troponin and LVEF (%)",
            "6": "Shift Table of Ophthalmological Examination Findings",
        }
    },

    # Section 14.4 - PK/PD Data
    "14.4.1": {
        "name": "Serum Concentrations",
        "sub_items": {
            "1": "Descriptive Statistics Serum Concentrations of DS-8201a",
            "2": "Descriptive Statistics Serum Concentrations of DS-8201a by Country",
            "3": "Descriptive Statistics Serum Concentrations of Total Anti-HER2 Antibody",
        }
    },
    "14.4.2": {
        "name": "Individual Plasma Concentrations",
        "sub_items": {
            "1": "Individual Plasma Concentrations of DS-8201a",
            "2": "Individual Plasma Concentrations of Total Anti-HER2 Antibody",
        }
    },
    "14.4.3": {
        "name": "Individual Serum Concentrations (other analytes)",
        "sub_items": {
            "1": "Individual Serum Concentrations of MAAA-1181a",
        }
    },
    "14.4.4": {
        "name": "Pharmacokinetic Parameters",
        "sub_items": {
            "1": "Descriptive Statistics PK Parameters of DS-8201a",
            "2": "Descriptive Statistics PK Parameters by Country",
        }
    },
    "14.4.7": {
        "name": "Immunogenicity (ADA)",
        "sub_items": {
            "1": "Summary of Anti-Drug Antibodies (ADA) Evaluation by Visit",
        }
    },
"14.4.8": {
        "name": "Biomarkers",
        "sub_items": {
            "1": "HER2 ECD/NEU Results",
        }
    },
}

# ICH E3 Section 14 Figure Templates
# Based on reference knowledge .knowledge/TLF/Pgm/
FIGURE_TEMPLATES = {
    "14.2.1": {
        "name": "Overall Survival Figures",
        "sub_items": {
            "1": "Kaplan-Meier Curves of Overall Survival by Treatment Group",
        }
    },
    "14.2.3": {
        "name": "Tumor Response Figures",
        "sub_items": {
            "3": "Forest Plot for Objective Response Rate (ORR)",
        }
    },
    "14.2.4": {
        "name": "Tumor Response Change Figures",
        "sub_items": {
            "1": "Waterfall Plot of Best Percent Change in Sum of Diameters from Baseline in Target Lesions",
            "2": "Spider Plot of Percent Change in Sum of Diameters from Baseline",
            "3": "Swimmer Plot of Tumor Response over Time",
        }
    },
    "14.3.3": {
        "name": "Laboratory Value Figures",
        "sub_items": {
            "1": "Box-Whisker Plots of Individual Selected Laboratory Tests",
            "3": "Line Plots of Individual Selected Laboratory Tests",
        }
    },
    "14.3.4": {
        "name": "Hepatotoxicity Figures",
        "sub_items": {
            "1": "Evaluation of Drug-induced Serious Hepatotoxicity (eDISH) Plot",
        }
    },
    "14.4.1": {
        "name": "PK Concentration Figures",
        "sub_items": {
            "1": "Plot of Mean (+/- SD) Serum Concentrations of DS-8201a by Dose Group - Linear Scale",
            "2": "Plot of Mean Serum Concentrations of DS-8201a by Dose Group in Semi-logarithmic Scale",
        }
    },
    "14.4.2": {
        "name": "Individual PK Concentration Figures",
        "sub_items": {
            "1": "Plot of Individual Plasma Concentrations of DS-8201a in Linear Scale",
        }
    },
}

# Standard Populations
POPULATIONS = [
    "All Screened Subjects",
    "Enrolled Analysis Set",
    "Safety Analysis Set",
    "Response Evaluable Set",
    "PK Analysis Set",
    "Full Analysis Set",
    "Per-Protocol Set",
]

def get_tlf_id(section: str, sub_section: str = "") -> str:
    """
    Generate TLF ID based on section and sub-section.

    Args:
        section: e.g., "14.1", "14.2", "14.3", "14.4"
        sub_section: e.g., "1", "2.1", "3.2.1"

    Returns:
        TLF ID string, e.g., "Table 14.1.1.1"
    """
    if "." not in section:
        return f"Table {section}"

    parts = section.split(".")
    if len(parts) < 2:
        return f"Table {section}"

    tlf_type = "Table" if parts[0] == "14" else "Listing" if parts[0] == "16" else "Figure"

    if sub_section:
        return f"{tlf_type} {section}.{sub_section}"
    return f"{tlf_type} {section}"


def get_all_tlf_ids() -> List[str]:
    """
    Get all possible TLF IDs based on ICH E3 structure.

    Returns:
        List of TLF ID strings
    """
    tlf_ids = []

    for section, section_info in TLF_TEMPLATES.items():
        if not section_info["sub_items"]:
            tlf_ids.append(f"Table {section}")
        else:
            for sub_item in section_info["sub_items"].keys():
                tlf_ids.append(f"Table {section}.{sub_item}")

    return tlf_ids


def match_sap_content_to_tlf(sap_keywords: List[str]) -> List[Dict]:
    """
    Match SAP content keywords to potential TLF IDs.

    Args:
        sap_keywords: List of keywords found in SAP (e.g., ['disposition', 'demographic', 'adverse event'])

    Returns:
        List of matched TLF info dicts with tlf_id, tlf_name, population
    """
    matches = []
    sap_keywords_lower = [kw.lower() for kw in sap_keywords]

    for section, section_info in TLF_TEMPLATES.items():
        tlf_name = section_info["name"]

        # Check if any keyword matches the section name
        for kw in sap_keywords_lower:
            if kw in tlf_name.lower():
                # Add base section
                matches.append({
                    "tlf_id": f"Table {section}",
                    "tlf_name": tlf_name,
                    "population": "Enrolled Analysis Set"  # Default
                })

                # Add sub-items
                for sub_item, sub_name in section_info["sub_items"].items():
                    matches.append({
                        "tlf_id": f"Table {section}.{sub_item}",
                        "tlf_name": sub_name,
                        "population": "Enrolled Analysis Set"
                    })
                break

    return matches


# Listing 16.2.x templates
LISTING_TEMPLATES = {
    "16.2.1": {
        "name": "Subject Disposition",
        "sub_items": {
            "1": "Subject Disposition",
            "2": "Study Sites, Principal Investigators, and Subject Accrual",
            "3": "Survival Follow-Up",
            "4": "Death by Subject",
        }
    },
    "16.2.2": {
        "name": "Inclusion/Exclusion",
        "sub_items": {
            "1": "Inclusion / Exclusion Criteria",
            "2": "Informed Consent",
            "3": "Subject Enrollment",
            "4": "Protocol Deviations",
        }
    },
    "16.2.3": {
        "name": "Analysis Sets",
        "sub_items": {
            "": "Subject Inclusion and Exclusion in Analysis Sets",
        }
    },
    "16.2.4": {
        "name": "Demographics",
        "sub_items": {
            "1": "Demographics",
            "2": "Pregnancy Test Results",
            "3.1": "Medical/Surgical History",
            "3.2": "Tobacco History",
            "4.1": "Primary Breast Cancer History",
            "4.2": "Prior Cancer Systemic Therapy",
            "4.3": "Prior Cancer Surgery",
            "4.4": "Prior Radiation Therapy",
            "5": "Prior/Concomitant Medications",
            "6": "Non-Drug Treatment/Procedures",
        }
    },
    "16.2.5": {
        "name": "Drug Administration",
        "sub_items": {
            "1.1": "Study Drug Administration",
            "1.2": "Study Drug Exposure",
            "2.1": "DS-8201a Pharmacokinetic Sample Collection Time and Results",
            "2.2": "Total Anti-HER2 Antibody Pharmacokinetic Sample Collection Time and Results",
            "2.3": "MAAA-1181a Pharmacokinetic Sample Collection Time and Results",
            "3.1": "DS-8201a Pharmacokinetic Parameters",
            "3.2": "Total Anti-HER2 Antibody Pharmacokinetic Parameters",
            "3.3": "MAAA-1181a Pharmacokinetic Parameters",
        }
    },
    "16.2.6": {
        "name": "Tumor Response",
        "sub_items": {
            "1.1": "Target Tumor Assessments by ICR",
            "1.2": "Non-Target Tumor Assessments by ICR",
            "1.3": "Target Tumor Assessments by Investigator",
            "1.4": "Non-Target Tumor Assessments by Investigator",
            "2.1": "Overall Tumor Response - RECIST by ICR",
            "2.2": "Overall Tumor Response - RECIST by Investigator",
            "3": "Progression-Free Survival (PFS) and Overall Survival (OS)",
            "4.1": "Subjects with CR, PR, or SD by ICR",
            "4.2": "Subjects with CR, PR, or SD by Investigator",
        }
    },
    "16.2.7": {
        "name": "Adverse Events",
        "sub_items": {
            "1": "Adverse Events",
            "2": "Serious Adverse Events",
            "3": "AEs Associated with Treatment Discontinuation",
            "4": "AEs Associated with Dose Reduced",
            "5": "AEs Associated with Drug Interrupted",
            "6": "AEs Associated with Death as Outcome",
            "7": "AEs of Special Interests",
            "8": "Potential Interstitial Lung Disease Events",
        }
    },
    "16.2.8": {
        "name": "Laboratory and Vital Signs",
        "sub_items": {
            "1.1": "Laboratory Parameters - Hematology",
            "1.2": "Laboratory Parameters - Blood Chemistry",
            "1.3": "Laboratory Parameters - Troponin",
            "1.4": "Laboratory Parameters - Urinalysis",
            "1.5": "Laboratory Parameters - Coagulation",
            "2.1": "Liver Chemistry Abnormalities",
            "2.2": "HIV Antibody",
            "3.1": "Vital Signs",
            "3.3": "Physical Examination",
            "3.4": "ECOG Performance Status",
            "3.6": "Echo/MUGA (LVEF) Assessments",
            "4.1": "Anti-Drug Antibodies (ADA)",
            "4.2": "HER2 ECD/NEU Results",
            "4.3": "Central and Local HER2 Expression Results at Screening",
        }
    },
}


if __name__ == "__main__":
    # Test: Get all possible TLF IDs
    print("=== ICH E3 TLF Knowledge Base ===")
    print(f"Total Table sections: {len(TLF_TEMPLATES)}")
    print(f"Total Listing sections: {len(LISTING_TEMPLATES)}")
    print()

    # Generate all possible TLF IDs
    all_ids = get_all_tlf_ids()
    print(f"Total possible Table TLF IDs: {len(all_ids)}")
    print("\nFirst 20 TLF IDs:")
    for tlf_id in all_ids[:20]:
        print(f"  {tlf_id}")

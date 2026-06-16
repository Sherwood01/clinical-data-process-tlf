"""
Listing Generator - Generate patient data listings (16.2.x).

Listings display individual subject-level data in a structured format
with column headers and sorted records. They serve as reference documents
supporting the tables in Section 14.

Key patterns:
- One line per record (subject-visit or subject-event)
- Columns show key variables for traceability
- Sorted by subject ID and visit/timepoint
"""

import pyreadstat
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


# ============================================================================
# Listing Definitions - maps listing ID to dataset and column configuration
# ============================================================================

LISTING_CONFIGS = {
    # 16.2.1 Study Administrative
    "16.2.1.1": {
        "name": "Subject Disposition",
        "datasets": ["adsl"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "COHORT", "ENRLFL", "SAFFL",
                    "TRTSDT", "TRTEDT", "EOSSTDT", "EOSSTN", "AGE", "SEX", "RACE"],
        "filters": [],
        "description": "Subject disposition and study completion status",
        "population": "Enrolled Analysis Set",
        "pdf_template": {
            "group_by": "COHORT",
            "rows_per_page": 30,
            "page_size": "letter",
            "source_data": "ADaM.ADSL",
            "columns": [
                {"name": "Cohort", "source": "COHORT", "width": 38},
                {"name": "Subject ID\n/Age/Sex", "source": "_combined_id", "width": 28},
                {"name": "First Dose Date / Last Dose Date\n(Study Day)", "source": "_dates", "width": 48},
                {"name": "Treatment\nDuration\n(Days)", "source": "_duration", "width": 22},
                {"name": "Study\nDuration\n(Days)", "source": "_study_duration", "width": 22},
                {"name": "Discontinued\nTreatment?", "source": "_discon", "width": 22},
                {"name": "Date of Subject's\nDiscontinuation", "source": "EOSSTDT", "width": 30},
                {"name": "Primary Reason for\nDiscontinuation", "source": "EOSSTT", "width": 35},
            ],
        }
    },
    "16.2.1.2": {
        "name": "Study Sites and Subject Accrual",
        "datasets": ["adsl"],
        "columns": ["SITEID", "COUNTRY", "USUBJID", "SUBJID", "RFICDT", "ARM"],
        "filters": [],
        "description": "Study sites, investigators, and subject enrollment",
        "population": "Enrolled Analysis Set",
        "pdf_template": {
            "group_by": "Site ID",
            "rows_per_page": 30,
            "data_mapping": {
                "Site ID": "Site ID",
                "Country": "Country",
                "Subject ID": "Subject ID",
                "Date of Informed Consent": "Date of Informed Consent",
                "Treatment Arm": "Treatment Arm",
            }
        }
    },
    "16.2.1.3": {
        "name": "Survival Follow-Up",
        "datasets": ["adtte", "adsl"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "PARAM", "AVAL", "CNSR",
                    "EVNTDESC", "ADT", "TRTSDT"],
        "filters": [],
        "description": "Survival follow-up data from ADTTE",
        "population": "Enrolled Analysis Set",
    },
    "16.2.1.4": {
        "name": "Death by Subject",
        "datasets": ["adsl", "adae"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "DTHFL", "DTHDT",
                    "DTHCAUSE", "AESOC", "AEDECOD"],
        "filters": [],
        "description": "Deaths by subject with cause",
        "population": "Enrolled Analysis Set",
    },

    # 16.2.2 Protocol / Eligibility
    "16.2.2.1": {
        "name": "Inclusion / Exclusion Criteria",
        "datasets": ["adsl"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "COUNTRY"],
        "filters": [],
        "description": "Inclusion/exclusion criteria evaluation",
        "population": "Enrolled Analysis Set",
    },
    "16.2.2.2": {
        "name": "Informed Consent",
        "datasets": ["adsl"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "COUNTRY", "RFICDT", "ARM"],
        "filters": [],
        "description": "Informed consent documentation",
        "population": "Enrolled Analysis Set",
    },
    "16.2.2.3": {
        "name": "Subject Enrollment",
        "datasets": ["adsl"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "COUNTRY", "ARM", "COHORT",
                    "RANDDT", "REGDT"],
        "filters": [],
        "description": "Subject enrollment and randomization",
        "population": "Enrolled Analysis Set",
    },
    "16.2.2.4": {
        "name": "Protocol Deviations",
        "datasets": ["addv"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "DVTERM", "DVCAT",
                    "DVSCAT", "DVSTDTC", "DVREAS"],
        "filters": [],
        "description": "Protocol deviations",
        "population": "Safety Analysis Set",
        "pdf_template": {
            "group_by": "USUBJID",
            "rows_per_page": 30,
            "headers": [
                [{"text": "Subject ID", "rowspan": 2}],
                [{"text": "Treatment Arm", "rowspan": 2}],
                [{"text": "Protocol Deviation", "rowspan": 2}],
                [{"text": "Category", "rowspan": 2}],
                [{"text": "Date", "rowspan": 2}],
                [{"text": "Reported Reason", "rowspan": 2}],
            ],
            "data_mapping": {
                "Subject ID": "SUBJID",
                "Treatment Arm": "ARM",
                "Protocol Deviation": "DVTERM",
                "Category": "DVCAT",
                "Date": "DVSTDTC",
                "Reported Reason": "DVREAS",
            }
        }
    },

    # 16.2.4 Subject Characteristics
    "16.2.4.1": {
        "name": "Demographics",
        "datasets": ["adsl"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "AGE", "AGEU", "SEX", "RACE",
                    "ARM", "COUNTRY", "BRTHDT"],
        "filters": [],
        "description": "Subject demographics",
        "population": "Enrolled Analysis Set",
        "pdf_template": {
            "group_by": "ARM",
            "rows_per_page": 30,
            "headers": [
                [{"text": "Subject ID", "rowspan": 2}],
                [{"text": "Age", "rowspan": 2}],
                [{"text": "Sex", "rowspan": 2}],
                [{"text": "Race", "rowspan": 2}],
                [{"text": "Country", "rowspan": 2}],
            ],
            "data_mapping": {
                "Subject ID": "SUBJID",
                "Age": "AGE",
                "Sex": "SEX",
                "Race": "RACE",
                "Country": "COUNTRY",
            }
        }
    },
    "16.2.4.2": {
        "name": "Pregnancy Test Results",
        "datasets": ["adlb"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "AVAL",
                    "AVISIT", "ADT"],
        "filters": ["PARAMCD=='PREGT'"],
        "description": "Pregnancy test results",
        "population": "Safety Analysis Set",
    },
    "16.2.4.3.1": {
        "name": "Medical/Surgical History",
        "datasets": ["admh"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "MHTERM", "MHCAT",
                    "MHSCAT", "MHSTDTC", "MHENDTC", "MHSEV"],
        "filters": [],
        "description": "Medical and surgical history",
        "population": "Safety Analysis Set",
        "pdf_template": {
            "group_by": "USUBJID",
            "rows_per_page": 30,
            "headers": [
                [{"text": "Subject ID", "rowspan": 2}],
                [{"text": "System Organ Class", "rowspan": 2}],
                [{"text": "Verbatim Term", "rowspan": 2}],
                [{"text": "Start Date", "rowspan": 2}],
                [{"text": "End Date", "rowspan": 2}],
            ],
            "data_mapping": {
                "Subject ID": "SUBJID",
                "System Organ Class": "MHCAT",
                "Verbatim Term": "MHTERM",
                "Start Date": "MHSTDTC",
                "End Date": "MHENDTC",
            }
        }
    },
    "16.2.4.3.2": {
        "name": "Tobacco History",
        "datasets": ["admh"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "MHTERM", "MHSCAT",
                    "MHSTDTC"],
        "filters": ["MHCAT=='TObacco USE'"],
        "description": "Tobacco use history",
        "population": "Safety Analysis Set",
    },
    "16.2.4.5": {
        "name": "Prior/Concomitant Medications",
        "datasets": ["adcm"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "CMTRT", "CMATC",
                    "CMCLAS", "CMINDC", "CMSTRT", "CMEND", "CMDOSU", "CMROUTE"],
        "filters": [],
        "description": "Prior and concomitant medications"
    },

    # 16.2.5 Exposure / PK
    "16.2.5.1.1": {
        "name": "Study Drug Administration",
        "datasets": ["adex"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "EXTRT", "EXDOSE",
                    "EXSTDTC", "EXENDTC", "EXLOT", "EXLOC"],
        "filters": [],
        "description": "Study drug administration details"
    },
    "16.2.5.1.2": {
        "name": "Study Drug Exposure",
        "datasets": ["adsl", "adex"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "TRTSDT", "TRTEDT",
                    "EXDOSE", "EXADJ"],
        "filters": [],
        "description": "Summary of study drug exposure"
    },
    "16.2.5.2.1": {
        "name": "Drug XXX Pharmacokinetic Sample Collection",
        "datasets": ["adpp"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PPTEST", "PARAM",
                    "ADT", "ADTM", "ARFTDT", "ARFTTM", "AVAL", "AVALRC"],
        "filters": ["PPCAT=='Drug XXX'"],
        "description": "PK sample collection time and results for Drug XXX"
    },
    "16.2.5.2.3": {
        "name": "MAAA-1181a Pharmacokinetic Sample Collection",
        "datasets": ["adpp"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PPTEST", "PARAM",
                    "ADT", "ADTM", "ARFTDT", "ARFTTM", "AVAL", "AVALRC"],
        "filters": ["PPCAT=='MAAA-1181a'"],
        "description": "PK sample collection time and results for MAAA-1181a"
    },
    "16.2.5.3.1": {
        "name": "Drug XXX Pharmacokinetic Parameters",
        "datasets": ["adpp"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PPTEST", "PARAM",
                    "AVAL", "AVALC"],
        "filters": ["PPCAT=='Drug XXX'"],
        "description": "PK parameters for Drug XXX"
    },
    "16.2.5.3.3": {
        "name": "MAAA-1181a Pharmacokinetic Parameters",
        "datasets": ["adpp"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PPTEST", "PARAM",
                    "AVAL", "AVALC"],
        "filters": ["PPCAT=='MAAA-1181a'"],
        "description": "PK parameters for MAAA-1181a"
    },

    # 16.2.6 Efficacy
    "16.2.6.1.1": {
        "name": "Target Tumor Assessments by ICR",
        "datasets": ["adrs"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "VISIT",
                    "TRSOLV", "TUMORID", "BASEDTM", "NEVALTM", "AVAL",
                    "CHG", "NRIND"],
        "filters": ["FASFL=='Y'"],
        "description": "Target lesion tumor assessments by ICR"
    },
    "16.2.6.1.3": {
        "name": "Target Tumor Assessments by Investigator",
        "datasets": ["adrs"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "VISIT",
                    "TRTVA", "TUMORID", "BASEDTM", "NEVALTM", "AVAL",
                    "CHG", "INVNRIND"],
        "filters": [],
        "description": "Target lesion tumor assessments by Investigator"
    },
    "16.2.6.2.1": {
        "name": "Overall Tumor Response - RECIST by ICR",
        "datasets": ["adrs"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "VISIT", "TRGRESP",
                    "NRIND", "NRLDCT", "NRTGTN", "NRTRN", "AVAL"],
        "filters": ["FASFL=='Y'"],
        "description": "Overall tumor response by ICR per RECIST 1.1"
    },
    "16.2.6.2.2": {
        "name": "Overall Tumor Response - RECIST by Investigator",
        "datasets": ["adrs"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "VISIT", "INVRESP",
                    "INVNRIND", "INVLDCT", "INVTGTN", "INVTRN", "AVAL"],
        "filters": [],
        "description": "Overall tumor response by Investigator per RECIST 1.1"
    },
    "16.2.6.3": {
        "name": "PFS and Overall Survival",
        "datasets": ["adtte"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "AVAL",
                    "CNSR", "EVNTDESC", "ADT"],
        "filters": [],
        "description": "PFS and OS event data"
    },
    "16.2.6.4.1": {
        "name": "Subjects with CR, PR, or SD by ICR",
        "datasets": ["adrs"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "VISIT", "TRGRESP",
                    "NRLDCT", "NRTRN", "CHG", "NRIND"],
        "filters": ["TRGRESP in ('CR','PR','SD')"],
        "description": "Subjects with CR/PR/SD response by ICR"
    },

    # 16.2.7 Safety - Adverse Events
    "16.2.7.1": {
        "name": "Adverse Events",
        "datasets": ["adae"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "TRTA", "AESOC",
                    "AEDECOD", "AETERM", "AEGRADE", "AESEV", "AEREL",
                    "AEOUT", "AESTDTC", "AEENDTC", "AESER", "AEDUR",
                    "AEACNOT", "SAEFL"],
        "filters": [],
        "description": "All adverse events (TEAEs)"
    },
    "16.2.7.2": {
        "name": "Serious Adverse Events",
        "datasets": ["adae"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "TRTA", "AESOC",
                    "AEDECOD", "AETERM", "AEGRADE", "AESEV", "AEREL",
                    "AEOUT", "AESTDTC", "AEENDTC", "AESER", "SERFL",
                    "AECONFK", "AECANCF"],
        "filters": ["AESER=='Y'"],
        "description": "Serious adverse events"
    },
    "16.2.7.3": {
        "name": "AEs Associated with Treatment Discontinuation",
        "datasets": ["adae"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "AESOC", "AEDECOD",
                    "AETERM", "AEGRADE", "AEREL", "AEOUT", "AESTDTC"],
        "filters": ["AEDECOD=='Treatment Discontinued'"],
        "description": "AEs leading to treatment discontinuation"
    },
    "16.2.7.4": {
        "name": "AEs Associated with Dose Reduced",
        "datasets": ["adae"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "AESOC", "AEDECOD",
                    "AETERM", "AEGRADE", "AEREL", "AEOUT", "AESTDTC"],
        "filters": ["AEDECOD=='Dose Reduced'"],
        "description": "AEs leading to dose reduction"
    },
    "16.2.7.5": {
        "name": "AEs Associated with Drug Interrupted",
        "datasets": ["adae"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "AESOC", "AEDECOD",
                    "AETERM", "AEGRADE", "AEREL", "AEOUT", "AESTDTC"],
        "filters": ["AEDECOD=='Drug Interrupted'"],
        "description": "AEs leading to drug interruption"
    },
    "16.2.7.6": {
        "name": "AEs Associated with Death as Outcome",
        "datasets": ["adae"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "AESOC", "AEDECOD",
                    "AETERM", "AEGRADE", "AESER", "AEREL", "AEOUT",
                    "AESTDTC", "AEENDTC"],
        "filters": ["AEOUT=='FATAL'"],
        "description": "AEs with fatal outcome"
    },
    "16.2.7.7": {
        "name": "AEs of Special Interest",
        "datasets": ["adae"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "AESOC", "AEDECOD",
                    "AETERM", "AEGRADE", "AESER", "AEREL", "AEOUT",
                    "AESTDTC", "AESCONC"],
        "filters": ["AESCONC=='Y'"],
        "description": "Adverse events of special interest"
    },
    "16.2.7.8": {
        "name": "Potential Interstitial Lung Disease Events",
        "datasets": ["adae"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "AESOC", "AEDECOD",
                    "AETERM", "AEGRADE", "AESER", "AEREL", "AEOUT",
                    "AESTDTC", "AEILDDG", "AEILOT"],
        "filters": ["AESOC=='Interstitial Lung Disease'"],
        "description": "Potential ILD events"
    },

    # 16.2.8 Safety - Labs / VS / PE
    "16.2.8.1.1": {
        "name": "Laboratory Parameters - Hematology",
        "datasets": ["adlb"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "AVISIT",
                    "AVAL", "AVALU", "BASE", "CHG", "ANRLO", "ANRHI",
                    "ATOXGR", "LBTOXGR"],
        "filters": ["PARAMCD in ('WBC','RBC','HGB','HCT','PLAT','NEUT','LYM','MON','EOS','BASO')"],
        "description": "Hematology laboratory values"
    },
    "16.2.8.1.2": {
        "name": "Laboratory Parameters - Blood Chemistry",
        "datasets": ["adlb"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "AVISIT",
                    "AVAL", "AVALU", "BASE", "CHG", "ANRLO", "ANRHI",
                    "ATOXGR", "LBTOXGR"],
        "filters": ["PARAMCD in ('ALT','AST','BILI','ALP','ALB','TP','CREAT','BUN','GLUC')"],
        "description": "Blood chemistry laboratory values"
    },
    "16.2.8.1.3": {
        "name": "Laboratory Parameters - Troponin",
        "datasets": ["adlb"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "AVISIT",
                    "AVAL", "AVALU", "BASE", "CHG", "ANRLO", "ANRHI",
                    "ATOXGR"],
        "filters": ["PARAMCD in ('TROP','TROPTH')"],
        "description": "Troponin laboratory values"
    },
    "16.2.8.1.4": {
        "name": "Laboratory Parameters - Urinalysis",
        "datasets": ["adlb"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "AVISIT",
                    "AVAL", "AVALC", "AVALU"],
        "filters": [],
        "description": "Urinalysis results"
    },
    "16.2.8.1.5": {
        "name": "Laboratory Parameters - Coagulation",
        "datasets": ["adlb"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "AVISIT",
                    "AVAL", "AVALU", "BASE", "CHG", "ANRLO", "ANRHI",
                    "ATOXGR"],
        "filters": ["PARAMCD in ('PT','INR','APTT','FIB')"],
        "description": "Coagulation laboratory values"
    },
    "16.2.8.2.1": {
        "name": "Liver Chemistry Abnormalities",
        "datasets": ["adlb"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "AVISIT",
                    "AVAL", "BASE", "CHG", "ULN", "MULT", "CRITFL",
                    "RBEST", "HYSTFL"],
        "filters": ["PARAMCD in ('ALT','AST','BILI')"],
        "description": "Liver chemistry abnormalities (Hy's Law)"
    },
    "16.2.8.3.1": {
        "name": "Vital Signs",
        "datasets": ["advs"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "VISIT",
                    "AVAL", "AVALU", "BASE", "CHG", "ANRLO", "ANRHI",
                    "POSTFL"],
        "filters": [],
        "description": "Vital signs measurements"
    },
    "16.2.8.3.3": {
        "name": "Physical Examination",
        "datasets": ["adpe"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PEBODSYS",
                    "PETEST", "PEORRES", "PESTRES", "VISIT", "PEDTC"],
        "filters": [],
        "description": "Physical examination findings"
    },
    "16.2.8.3.6": {
        "name": "Echo/MUGA (LVEF) Assessments",
        "datasets": ["adeg"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PARAM", "VISIT",
                    "AVAL", "BASE", "CHG", "ANRLO", "QTLBQL", "EGNORM"],
        "filters": ["PARAMCD in ('LVEF','EF')"],
        "description": "Cardiac function (LVEF) by echo/MUGA"
    },

    # 16.2.8.4 Immunogenicity
    "16.2.8.4.1": {
        "name": "Anti-Drug Antibodies (ADA)",
        "datasets": ["adpp"],
        "columns": ["USUBJID", "SUBJID", "SITEID", "ARM", "PPTEST", "PARAM",
                    "AVISIT", "AVAL", "AVALRC"],
        "filters": ["PPCAT in ('ADA','NAB')"],
        "description": "Anti-drug antibody results"
    },
}


# ============================================================================
# Column Display Name Mapping
# ============================================================================

COLUMN_DISPLAY_NAMES = {
    # Subject ID
    "USUBJID": "Unique Subject ID",
    "SUBJID": "Subject ID",
    "SITEID": "Site ID",
    "SITENUM": "Site Number",

    # Demographics
    "AGE": "Age",
    "AGEU": "Age Unit",
    "SEX": "Sex",
    "RACE": "Race",
    "ETHNIC": "Ethnicity",
    "COUNTRY": "Country",
    "BRTHDT": "Birth Date",

    # Treatment
    "ARM": "Treatment Arm",
    "TRTA": "Actual Treatment",
    "TRTP": "Planned Treatment",
    "COHORT": "Cohort",

    # Dates
    "RFICDT": "Date of Informed Consent",
    "RANDDT": "Randomization Date",
    "REGDT": "Registration Date",
    "TRTSDT": "Treatment Start Date",
    "TRTEDT": "Treatment End Date",
    "EOSSTDT": "End of Study Date",
    "DTHDT": "Death Date",
    "ADT": "Analysis Date",
    "VISIT": "Visit",
    "AVISIT": "Analysis Visit",
    "AESTDTC": "AE Start Date",
    "AEENDTC": "AE End Date",

    # AE
    "AESOC": "System Organ Class",
    "AEDECOD": "Preferred Term",
    "AETERM": "Verbatim Term",
    "AEGRADE": "CTCAE Grade",
    "AESEV": "Severity",
    "AEREL": "Relationship to Study Drug",
    "AEOUT": "Outcome",
    "AESER": "Serious",
    "AEDUR": "Duration (days)",
    "AECONFK": "SAE Confirmed",
    "AECANCF": "SAE Confounded",
    "SAEFL": "SAE Flag",
    "AESCONC": "ESI Flag",
    "AEILDDG": "ILD Grade",
    "AEILOT": "ILD Outcome",
    "TRTAFL": "Treatment-Emergent",

    # Lab
    "PARAM": "Parameter",
    "PARAMCD": "Parameter Code",
    "AVAL": "Value",
    "AVALU": "Unit",
    "BASE": "Baseline",
    "CHG": "Change from Baseline",
    "ANRLO": "ANR Low",
    "ANRHI": "ANR High",
    "ATOXGR": "Toxicity Grade",
    "LBTOXGR": "CTCAE Grade",

    # Tumor
    "TRSOLV": "Overall Response (ICR)",
    "TRTVA": "Overall Response (INV)",
    "TRGRESP": "Best Overall Response (ICR)",
    "INVRESP": "Best Overall Response (INV)",
    "TUMORID": "Tumor ID",
    "BASEDTM": "Baseline Date",
    "NEVALTM": "Evaluation Date",
    "NRLDCT": "Target Lesion Sum (mm)",
    "NRTRN": "Best Change from Baseline",
    "NRIND": "Investigator Assessment",
    "INVNRIND": "INV Assessment",
    "INVLDCT": "INV Target Lesion (mm)",
    "INVTGTN": "INV Best Change",

    # PK
    "PPTEST": "Test",
    "PPCAT": "Category",
    "ADTM": "Date/Time",
    "ARFTDT": "Reference Date/Time",
    "ARFTTM": "Reference Time",
    "AVALRC": "Result Character",

    # ECG
    "EGNORM": "ECG Interpretation",
    "QTLBQL": "QT/QLB Ratio",

    # Misc
    "EXTRT": "Drug",
    "EXDOSE": "Dose",
    "EXLOT": "Lot Number",
    "EXLOC": "Injection Site",
    "EXADJ": "Dose Adjusted",
    "TRTDURD": "Treatment Duration (days)",

    # Status flags
    "ENRLFL": "Enrolled",
    "SAFFL": "Safety Analysis Flag",
    "FASFL": "Full Analysis Set Flag",
    "PKFL": "PK Population Flag",
    "CNSR": "Censored",
    "EVNTDESC": "Event Description",
    "DTHFL": "Death Flag",
    "DTHCAUSE": "Primary Cause of Death",
    "SERFL": "Serious Flag",
    "CRITFL": "Hy's Law Criterion",
    "RBEST": "Row Best",
    "HYSTFL": "Hy's Law",
    "POSTFL": "Post-Infusion",
    "ULN": "Upper Limit Normal",
    "MULT": "Multiple of ULN",

    # Deviation
    "DVTERM": "Deviation Term",
    "DVCAT": "Category",
    "DVSCAT": "Subcategory",
    "DVSTDTC": "Date",
    "DVREAS": "Reason",

    # Medical History
    "MHTERM": "History Term",
    "MHCAT": "Category",
    "MHSCAT": "Subcategory",
    "MHSTDTC": "Start Date",
    "MHENDTC": "End Date",
    "MHSEV": "Severity",

    # Medication
    "CMTRT": "Medication",
    "CMATC": "Therapeutic Class",
    "CMCLAS": "Drug Class",
    "CMINDC": "Indication",
    "CMSTRT": "Start Date",
    "CMEND": "End Date",
    "CMDOSU": "Dose",
    "CMROUTE": "Route",

    # Physical Exam
    "PEBODSYS": "Body System",
    "PETEST": "Exam Test",
    "PEORRES": "Finding",
    "PESTRES": "Standardized Result",
    "PEDTC": "Date",
}


# ============================================================================
# Listing Analyzer
# ============================================================================

class ListingAnalyzer:
    """
    Base analyzer for generating patient data listings.

    Listings differ from tables in that they show raw data records
    with subject-level detail rather than aggregated statistics.
    """

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self._datasets_cache = {}

    def _load_dataset(self, name: str) -> pd.DataFrame:
        """Load dataset with caching."""
        if name not in self._datasets_cache:
            path = self.data_dir / f"{name.lower()}.sas7bdat"
            if path.exists():
                self._datasets_cache[name], _ = pyreadstat.read_sas7bdat(str(path))
            else:
                raise FileNotFoundError(f"Dataset not found: {path}")
        return self._datasets_cache[name]

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure column names are strings (pandas reads SAS with bytes)."""
        df = df.copy()
        df.columns = [str(c) for c in df.columns]
        # Decode byte strings if needed
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = df[col].apply(
                        lambda x: x.decode() if isinstance(x, bytes) else x
                    )
                except:
                    pass
        return df

    def _format_value(self, val) -> str:
        """Format a single value for display."""
        if pd.isna(val):
            return ""
        if isinstance(val, bytes):
            val = val.decode()
        if isinstance(val, float):
            if np.isnan(val):
                return ""
            # Format floats appropriately
            if abs(val) >= 1000:
                return f"{val:.1f}"
            elif abs(val) >= 1:
                return f"{val:.2f}"
            else:
                return f"{val:.4f}"
        return str(val)

    def _filter_dataframe(self, df: pd.DataFrame, filter_str: str) -> pd.DataFrame:
        """Apply a simple filter to dataframe."""
        if not filter_str:
            return df
        try:
            # Handle simple PARAMCD in (...) filters
            if 'PARAMCD in' in filter_str:
                import re
                match = re.search(r"PARAMCD in \(([^)]+)\)", filter_str)
                if match:
                    values = [v.strip().strip("'\"") for v in match.group(1).split(',')]
                    return df[df['PARAMCD'].isin(values)]
            elif 'PPCAT in' in filter_str:
                import re
                match = re.search(r"PPCAT in \(([^)]+)\)", filter_str)
                if match:
                    values = [v.strip().strip("'\"") for v in match.group(1).split(',')]
                    return df[df['PPCAT'].isin(values)]
            elif 'TRGRESP in' in filter_str:
                import re
                match = re.search(r"TRGRESP in \(([^)]+)\)", filter_str)
                if match:
                    values = [v.strip().strip("'\"") for v in match.group(1).split(',')]
                    return df[df['TRGRESP'].isin(values)]
            elif 'AESOC==' in filter_str:
                import re
                match = re.search(r"AESOC=='([^']+)'", filter_str)
                if match:
                    return df[df['AESOC'] == match.group(1)]
            elif 'AESER==' in filter_str:
                import re
                match = re.search(r"AESER=='([^']+)'", filter_str)
                if match:
                    return df[df['AESER'] == match.group(1)]
            elif 'AEOUT==' in filter_str:
                import re
                match = re.search(r"AEOUT=='([^']+)'", filter_str)
                if match:
                    return df[df['AEOUT'] == match.group(1)]
            elif 'AESCONC==' in filter_str:
                import re
                match = re.search(r"AESCONC=='([^']+)'", filter_str)
                if match:
                    return df[df['AESCONC'] == match.group(1)]
            elif 'FASFL==' in filter_str:
                import re
                match = re.search(r"FASFL=='([^']+)'", filter_str)
                if match:
                    return df[df['FASFL'] == match.group(1)]
        except Exception:
            pass
        return df

    def generate_listing(self, listing_id: str) -> Dict[str, Any]:
        """
        Generate a patient data listing.

        Args:
            listing_id: e.g. "16.2.7.1" for AE listing

        Returns:
            Dict with:
                - header: list of display column names
                - columns: list of source column names
                - data: list of row dicts
                - total_records: total number of records
        """
        config = LISTING_CONFIGS.get(listing_id)
        if not config:
            raise ValueError(f"Unknown listing: {listing_id}")

        # Load all required datasets
        datasets = {}
        for ds_name in config['datasets']:
            try:
                df = self._load_dataset(ds_name)
                datasets[ds_name] = self._normalize_column_names(df)
            except FileNotFoundError:
                # Return empty result if dataset not available
                return {
                    'listing_id': listing_id,
                    'name': config['name'],
                    'header': config['columns'],
                    'columns': config['columns'],
                    'data': [],
                    'total_records': 0,
                    'message': f"Dataset {ds_name} not available"
                }

        # Start with primary dataset (first in list)
        primary_ds = config['datasets'][0]
        result_df = datasets[primary_ds].copy()

        # If secondary datasets exist and have common keys, show combined
        # For simplicity, we'll show primary dataset records
        # A more advanced implementation would do proper joins

        # Apply filters
        for filter_str in config['filters']:
            result_df = self._filter_dataframe(result_df, filter_str)

        # Select requested columns (intersection with available columns)
        available_cols = set(result_df.columns)
        requested_cols = [c for c in config['columns'] if c in available_cols]

        # If no requested columns found, try to find similar column names
        if not requested_cols:
            # Try column mapping variations
            for col in config['columns']:
                if col in available_cols:
                    requested_cols.append(col)
                else:
                    # Try without prefix
                    for avail in available_cols:
                        if col.replace('AE', '').lower() in avail.lower():
                            requested_cols.append(avail)
                            break

        # Sort by subject and visit
        sort_cols = []
        if 'USUBJID' in result_df.columns:
            sort_cols.append('USUBJID')
        if 'VISIT' in result_df.columns:
            sort_cols.append('VISIT')
        elif 'AVISITN' in result_df.columns:
            sort_cols.append('AVISITN')
        elif 'ADT' in result_df.columns:
            sort_cols.append('ADT')

        if sort_cols:
            try:
                result_df = result_df.sort_values(sort_cols)
            except:
                pass

        # Build output data
        header = [COLUMN_DISPLAY_NAMES.get(c, c) for c in requested_cols]
        data = []
        for _, row in result_df.iterrows():
            formatted_row = {COLUMN_DISPLAY_NAMES.get(c, c): self._format_value(row.get(c, ''))
                             for c in requested_cols}
            # Add original SAS column names for reference
            for c in requested_cols:
                disp = COLUMN_DISPLAY_NAMES.get(c, c)
                if disp != c:
                    formatted_row[c] = formatted_row.get(disp, '')
            data.append(formatted_row)

        return {
            'listing_id': listing_id,
            'name': config['name'],
            'header': header,
            'columns': requested_cols,
            'data': data,
            'total_records': len(data),
            'message': None
        }


# ============================================================================
# Listing Output Generator
# ============================================================================

class RTFGenerator:
    """Generate SAS-style RTF listings matching reference format."""

    def __init__(self):
        # Full color table matching SAS output
        self.color_table = r"{\colortbl;" + "\n" + \
                          r"\red0\green0\blue0;" + "\n" + \
                          r"\red0\green0\blue255;" + "\n" + \
                          r"\red0\green255\blue255;" + "\n" + \
                          r"\red0\green255\blue0;" + "\n" + \
                          r"\red255\green0\blue255;" + "\n" + \
                          r"\red255\green0\blue0;" + "\n" + \
                          r"\red255\green255\blue0;" + "\n" + \
                          r"\red255\green255\blue255;" + "\n" + \
                          r"\red0\green0\blue128;" + "\n" + \
                          r"\red0\green128\blue128;" + "\n" + \
                          r"\red0\green128\blue0;" + "\n" + \
                          r"\red128\green0\blue128;" + "\n" + \
                          r"\red128\green0\blue0;" + "\n" + \
                          r"\red128\green128\blue0;" + "\n" + \
                          r"\red128\green128\blue128;" + "\n" + \
                          r"\red192\green192\blue192;" + "\n" + \
                          r"}"
        self.font_table = r"{\fonttbl" + "\n" + \
                          r"{\f1\froman\fprq2\fcharset0 Times;}" + "\n" + \
                          r"{\f2\fmodern\fprq1\fcharset0 Courier;}" + "\n" + \
                          r"{\f3\fswiss\fprq2\fcharset0 Arial;}" + "\n" + \
                          r"}"
        self.page_width = 15840  # twips (letter width)
        self.page_height = 12240  # twips (letter height)
        self.margin = 1440  # 1 inch margins

    def _escape_rtf(self, text: str) -> str:
        """Escape special RTF characters."""
        if not isinstance(text, str):
            text = str(text) if text else ""
        text = text.replace('\\', '\\\\')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        return text

    def _cell_widths_from_data(self, header: List[str], data: List[Dict],
                                column_configs: List[Dict]) -> List[int]:
        """Calculate column widths based on content and column configs."""
        # Default: estimate text width in twips (1 char ≈ 7 twips at 9pt)
        char_width = 7
        available = self.page_width - (2 * self.margin)
        n_cols = len(header)

        # Calculate min widths from header
        widths = [min(len(h) * char_width, available // n_cols) for h in header]

        # Adjust based on column configs
        for i, config in enumerate(column_configs):
            if config.get('width'):
                widths[i] = config['width']
            if config.get('span'):
                # Merge with next column
                span = config['span']
                total_span = sum(widths[i:i+span])
                for j in range(i, i+span):
                    if j < len(widths):
                        pass  # Will handle span later

        # Ensure total doesn't exceed available
        total = sum(widths)
        if total > available:
            scale = available / total
            widths = [int(w * scale) for w in widths]

        return widths

    def _make_title_row(self, listing_id: str, name: str, protocol: str,
                        company: str, run_date: str, total_pages: int,
                        analysis_set: str, available_width: int) -> List[str]:
        """Create the SAS-style title row with company info, protocol, page#."""
        cell_props = r"\cltxlrtb\clvertalb\clcbpat8\clpadt29\clpadft3\clpadr29\clpadfr3"

        rows = []
        # Title row - full width
        rows.append(f"\\trowd\\trkeep\\trhdr\\trqc\\{cell_props}\\cellx{available_width}")

        # Multi-line title content: company left, listing filename right, then protocol/rundate,
        # then dry run/page info, then listing title and analysis set
        title_content = (
            f"\\pard\\plain\\intbl\\keepn\\sb29\\sa29\\ql\\f3\\fs18\\cf1{{"
            f"\\animtext0\\ul0\\strike0\\b0\\i0\\f3\\fs18\\cf1 {self._escape_rtf(company)}"
            f"\\~\\tqc\\tx6480\\tab\\~ "
            f"\\tqr\\tx12830\\tab Listing\\~{listing_id}.sas{{\\line}}"
            f"Protocol\\~{protocol}\\~\\tqr\\tx12830\\tab\\tab Run\\~Date\\~Time:\\~{run_date}{{"
            f"\\line}}Dry\\~Run\\~(Data\\~Cut\\~Date:\\~YYYY-MM-DD)\\~\\tqr\\tx12830\\tab\\tab Page\\~1\\~of\\~{total_pages}{{"
            f"\\line}}"
            f"\\par\\qc\\animtext0\\ul0\\strike0\\b0\\i0\\f3\\fs18\\cf1 Listing\\~{listing_id}:\\~{self._escape_rtf(name)}{{\\line}}"
            f"{self._escape_rtf(analysis_set)}{{\\line}}"
            f"\\brdrb\\brdrhair\\cell}}\\{{row}}"
        )
        rows.append(title_content)
        return rows

    def _make_header_row(self, header: List[str], col_widths: List[int]) -> List[str]:
        """Create column header row with borders."""
        rows = []
        rows.append(f"\\trowd\\trkeep\\trhdr\\trqc")

        # Cell definitions with borders
        for i, w in enumerate(col_widths):
            prev = sum(col_widths[:i])
            cell_def = (
                f"\\clbrdrb\\brdrs\\brdrw1\\brdrcf1\\cltxlrtb\\clvertalb\\clcbpat8"
                f"\\clpadt29\\clpadft3\\clpadr29\\clpadfr3\\cellx{prev + w}"
            )
            rows.append(cell_def)

        # Cell content
        for i, h in enumerate(header):
            rows.append(
                f"\\pard\\plain\\intbl\\keepn\\sb29\\sa29\\qc\\f3\\fs18\\cf1{{{self._escape_rtf(h)}\\cell}}"
            )
        rows.append(r"{\row}")
        return rows

    def _make_data_row(self, row: Dict, header: List[str],
                        col_widths: List[int]) -> List[str]:
        """Create a data row."""
        rows = []
        rows.append(f"\\trowd\\trkeep\\trqc")

        # Cell definitions
        for i, w in enumerate(col_widths):
            prev = sum(col_widths[:i])
            cell_def = (
                f"\\cltxlrtb\\clvertalt\\clcbpat8"
                f"\\clpadt29\\clpadft3\\clpadr29\\clpadfr3\\cellx{prev + w}"
            )
            rows.append(cell_def)

        # Cell content - left aligned
        for i, h in enumerate(header):
            val = str(row.get(h, '')) if row.get(h) is not None else ''
            rows.append(
                f"\\pard\\plain\\intbl\\sb29\\sa29\\ql\\f3\\fs18\\cf1{{{self._escape_rtf(val)}\\cell}}"
            )
        rows.append(r"{\row}")
        return rows

    def generate_rtf(self, listing_data: Dict[str, Any], output_path: str,
                     protocol: str = "xxxx-x-xxxx",
                     company: str = "Daiichi Sankyo, Inc.",
                     analysis_set: str = None):
        """Generate SAS-style RTF listing matching reference format exactly."""
        import math

        header = listing_data['header']
        data = listing_data['data']
        listing_id = listing_data.get('listing_id', '16.2.X.X')
        name = listing_data.get('name', 'Subject Listing')
        total_records = listing_data.get('total_records', len(data))

        if analysis_set is None:
            analysis_set = listing_data.get('population', 'Safety Analysis Set')

        available_width = self.page_width - (2 * self.margin)
        total_pages = max(1, math.ceil(total_records / 30))
        run_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Calculate smart column widths based on content
        col_widths = self._calculate_col_widths(header, data, available_width)

        # Build RTF
        rtf = []
        # Header
        rtf.append(r"{\rtf1\ansi\ansicpg1252\uc1\deff0\deflang1033\deflangfe1033")
        rtf.append(self.font_table)
        rtf.append(self.color_table)
        rtf.append(r"}{\stylesheet{\widctlpar\adjustright\fs20\cgrid\snext0 Normal;}{\*\cs10\additive Default Paragraph Font;}")
        info_str = (r"}{\info{\title Version 9.4 SAS System Output}"
                    r"{\author SAS Version 9.4}{\operator SAS Version 9.4}"
                    r"{\version1}{\creatim")
        now = datetime.now()
        info_str += f"\\yr{now.year}\\mo{now.month}\\dy{now.day}\\hr{now.hour}\\min{now.minute}\\sec{now.second}}}"
        rtf.append(info_str)
        rtf.append(f"\\widowctrl\\ftnbj\\aenddoc\\formshade\\viewkind1\\viewscale100"
                   f"\\pgbrdrhead\\pgbrdrfoot\\fet0\\paperw{self.page_width}\\paperh{self.page_height}"
                   f"\\margl{self.margin}\\margr{self.margin}\\margt1008\\margb1008")
        rtf.append(f"\\sectd\\linex0\\endnhere\\pgwsxn{self.page_width}\\pghsxn{self.page_height}"
                   f"\\lndscpsxn\\headery1008\\footery1008\\marglsxn{self.margin}\\margrsxn{self.margin}"
                   f"\\margtsxn1008\\margbsxn1008")

        # Empty header/footer (page info is in title row)
        rtf.append(r"{\header\pard\plain\qc{}}")
        rtf.append(r"{\footer\pard\plain\qc{}}")

        # Bookmarks
        rtf.append(r"{\upr{\*\bkmkstart IDX}{\*\ud{\*\bkmkstart IDX}}}{\*\bkmkend IDX}")

        # Title row
        rtf.extend(self._make_title_row(
            listing_id, name, protocol, company, run_date,
            total_pages, analysis_set, available_width
        ))

        # Column header row
        rtf.extend(self._make_header_row(header, col_widths))

        # Data rows
        for row in data:
            rtf.extend(self._make_data_row(row, header, col_widths))

        rtf.append("}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(rtf))
        print(f"  RTF: {output_path}")

    def _calculate_col_widths(self, header: List[str], data: List[Dict],
                              available: int) -> List[int]:
        """Calculate column widths based on header and data content."""
        import math

        n_cols = len(header)
        if n_cols == 0:
            return []

        # Sample data for width calculation
        sample_size = min(len(data), 50)
        sampled_data = data[:sample_size] if data else []

        # Calculate ideal widths based on content
        widths = []
        for i, h in enumerate(header):
            # Start with header length
            max_len = len(h)

            # Check data content
            for row in sampled_data:
                val = str(row.get(h, '')) if row.get(h) is not None else ''
                # Handle multi-line values
                for line in val.split('\n'):
                    max_len = max(max_len, len(line))

            # Convert to twips (roughly 7-8 twips per char at 9pt Arial)
            width = max(max_len * 8, 600)
            widths.append(width)

        # Scale down if total exceeds available
        total = sum(widths)
        if total > available:
            # Proportionally scale down
            scale = available / total
            widths = [max(int(w * scale), 500) for w in widths]

        # Ensure total equals available (adjust last column)
        diff = available - sum(widths)
        if diff != 0 and widths:
            widths[-1] += diff

        return widths


class PDFListingGenerator:
    """Generate professional PDF listings using reportlab with SAS-style formatting."""

    def __init__(self):
        # Use A3 landscape dimensions
        self.page_width = 420.0  # mm (A3 landscape width)
        self.page_height = 297.0  # mm (A3 landscape height)
        self.margin_left = 15.0
        self.margin_right = 15.0
        self.margin_top = 25.0
        self.margin_bottom = 20.0
        self.rows_per_page = 35

    def generate_pdf(self, listing_data: Dict[str, Any], output_path: str,
                    protocol: str = "xxxx-x-xxxx",
                    company: str = "Daiichi Sankyo, Inc.",
                    analysis_set: str = None):
        """Generate PDF listing matching SAS-style RTF format exactly."""
        from reportlab.lib import colors
        from reportlab.lib.units import mm, inch
        from reportlab.pdfgen import canvas as pdfcanvas

        listing_id = listing_data.get('listing_id', '16.2.X.X')
        name = listing_data.get('name', 'Subject Listing')
        data = listing_data['data']
        total_records = len(data)

        if analysis_set is None:
            analysis_set = listing_data.get('population', 'Safety Analysis Set')

        run_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Get template from LISTING_CONFIGS based on listing_id
        template = LISTING_CONFIGS.get(listing_id, {}).get('pdf_template', {})

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Use US Letter landscape dimensions (twips: 15840 x 12240)
        page_w = 11 * inch  # 11 inches wide (landscape letter)
        page_h = 8.5 * inch  # 8.5 inches tall
        margin = 0.75 * inch  # increased margin

        # Column definitions from template
        if template and 'columns' in template:
            col_defs = template['columns']
        else:
            col_defs = [{"name": h, "source": h, "width": 30} for h in listing_data['header']]

        # Compute derived columns
        enriched_data = [self._enrich_row(row, col_defs) for row in data]

        # Calculate column widths in points (1 pt = 1/72 inch)
        # Available width: page_w - 2*margin
        available_w = page_w - 2 * margin

        # Use exact column widths from template, scale if needed
        col_widths_pts = []
        template_widths = [col.get('width', 30) for col in col_defs]
        # Convert mm to pts (1 mm = 2.835 pts)
        col_widths_pts = [w * 2.835 for w in template_widths]

        total_cols = sum(col_widths_pts)
        if total_cols > available_w:
            scale = available_w / total_cols
            col_widths_pts = [w * scale for w in col_widths_pts]

        # Last column fills remaining space
        if sum(col_widths_pts) < available_w:
            diff = available_w - sum(col_widths_pts)
            col_widths_pts[-1] += diff

        # Group data
        group_by = template.get('group_by')
        rows_per_page = template.get('rows_per_page', 30)

        if group_by:
            grouped = self._group_data_by(enriched_data, group_by, col_defs)
        else:
            grouped = [(None, enriched_data)]

        # Flatten with group markers
        flat_data = []
        for group_label, group_rows in grouped:
            if group_label:
                flat_data.append(('GROUP', group_label))
            for row in group_rows:
                flat_data.append(('DATA', row))

        # Pagination
        pages = []
        current_page = []
        current_count = 0
        data_rows_per_page = rows_per_page - 1  # header row

        for item in flat_data:
            if current_count >= data_rows_per_page:
                pages.append(current_page)
                current_page = []
                current_count = 0
            current_page.append(item)
            current_count += 1

        if current_page:
            pages.append(current_page)

        total_pages = len(pages)

        # Font settings matching RTF (9pt Helvetica = fs18/2 = 9pt)
        font_size = 9
        font_name = 'Helvetica'
        bold_font = 'Helvetica-Bold'
        header_font_size = 8

        # Use canvas for precise control
        c = pdfcanvas.Canvas(output_path, pagesize=(page_w, page_h))

        for page_num, page_data in enumerate(pages, start=1):
            if page_num > 1:
                c.showPage()

            # Content area
            top = page_h - margin
            left = margin

            # ===== TITLE BLOCK =====
            line_h = 14  # line height

            # Title box - NO fill, just text
            title_y = top - line_h * 3

            c.setFont(bold_font, header_font_size)
            c.setFillColor(colors.black)

            # Line 1: Company left, Listing filename right
            c.drawString(left + 3, top - line_h + 2, company)
            c.drawRightString(left + available_w - 3, top - line_h + 2,
                             f"Listing {listing_id}.sas")

            # Line 2: Protocol, Run Date
            c.setFont(font_name, header_font_size)
            c.drawString(left + 3, top - line_h * 2 + 2, f"Protocol: {protocol}")
            c.drawRightString(left + available_w - 3, top - line_h * 2 + 2,
                             f"Run Date Time: {run_date}")

            # Line 3: Dry Run, Page X of Y
            c.drawString(left + 3, top - line_h * 3 + 2, "Dry Run (Data Cut Date: YYYY-MM-DD)")
            c.drawRightString(left + available_w - 3, top - line_h * 3 + 2,
                             f"Page {page_num} of {total_pages}")

            # Bottom border on title block
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.line(left, title_y, left + available_w, title_y)

            # ===== LISTING TITLE BLOCK =====
            subtitle_y = title_y - line_h * 2
            c.setFont(bold_font, header_font_size)

            # Listing title centered
            title_text = f"Listing {listing_id}: {name}"
            c.drawCentredString(left + available_w / 2, subtitle_y + line_h + 2, title_text)

            # Analysis set centered below
            c.setFont(font_name, header_font_size)
            c.drawCentredString(left + available_w / 2, subtitle_y + 2, analysis_set)

            # Bottom border
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.line(left, subtitle_y, left + available_w, subtitle_y)

            # ===== COLUMN HEADER ROW =====
            header_y = subtitle_y - line_h - 4

            # NO gray background for header
            c.setFillColor(colors.black)
            c.setFont(bold_font, header_font_size)

            current_x = left + 3
            for i, col in enumerate(col_defs):
                col_w = col_widths_pts[i]
                col_name = col['name']
                # Handle multi-line headers (split by \n)
                lines = col_name.split('\n')
                if len(lines) == 1:
                    c.drawCentredString(current_x + col_w / 2, header_y, lines[0])
                else:
                    # Multi-line: center the middle
                    total_h = len(lines) * (header_font_size + 1)
                    start_y = header_y + (len(lines) - 1) * (header_font_size + 1) / 2 + 3
                    for j, line in enumerate(lines):
                        c.drawCentredString(current_x + col_w / 2, start_y - j * (header_font_size + 1), line)

                current_x += col_w

            # Header bottom border
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.line(left, header_y - font_size - 5, left + available_w, header_y - font_size - 5)

            # ===== DATA ROWS =====
            row_y = header_y - font_size - 10
            row_height = font_size + 5

            for item in page_data:
                if item[0] == 'GROUP':
                    # Group header - NO background, just text
                    c.setFillColor(colors.black)
                    c.setFont(bold_font, header_font_size)
                    c.drawString(left + 3, row_y, item[1])
                    row_y -= row_height + 1
                else:
                    row = item[1]
                    c.setFont(font_name, font_size)

                    current_x = left + 3
                    for i, col in enumerate(col_defs):
                        col_w = col_widths_pts[i]
                        src = col['source']
                        if src.startswith('_'):
                            val = str(row.get(src, ''))
                        else:
                            val = str(row.get(src, '')) if row.get(src) is not None else ''

                        # Alignment: numbers center, text left
                        # Check if it's a number-like value
                        try:
                            float(val.replace(',', '').replace(' ', ''))
                            align = 'center'
                        except:
                            align = 'left'

                        if align == 'center':
                            c.drawCentredString(current_x + col_w / 2, row_y, val)
                        else:
                            # Left align with padding
                            c.drawString(current_x, row_y, val[:int(col_w / (font_size * 0.5))])  # truncate

                        current_x += col_w

                    row_y -= row_height

            # ===== BOTTOM BORDER / FOOTER LINE =====
            # NO borders - just bottom line under data
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.line(left, row_y + font_size, left + available_w, row_y + font_size)

            # ===== FOOTER =====
            footer_y = margin / 2
            c.setFont(font_name, 7)
            c.setFillColor(colors.black)
            source_data = template.get('source_data', 'ADaM.ADSL')
            c.drawString(left, footer_y, f"Source Data: {source_data}")

        c.save()
        print(f"  PDF: {output_path}")

    def _enrich_row(self, row: Dict, col_defs: List[Dict]) -> Dict:
        """Enrich a data row with computed/derived columns."""
        enriched = dict(row)

        for col in col_defs:
            src = col['source']
            if src == '_combined_id':
                # Format: SUBJID/Age/Sex
                subj = str(row.get('Subject ID', row.get('SUBJID', '')))
                age = str(row.get('Age', row.get('AGE', '')))
                sex = str(row.get('Sex', row.get('SEX', '')))
                enriched['_combined_id'] = f"{subj}/{age}/{sex}"
            elif src == '_dates':
                # Format: TRTSDT/TRTEDT (Study Day)
                start = self._format_date(row.get('Treatment Start Date', row.get('TRTSDT', '')))
                end = self._format_date(row.get('Treatment End Date', row.get('TRTEDT', '')))
                # Calculate study day
                trtsdt = row.get('TRTSDT', row.get('Treatment Start Date', ''))
                trtedt = row.get('TRTEDT', row.get('Treatment End Date', ''))
                if trtsdt and trtedt:
                    try:
                        from datetime import datetime
                        s = self._parse_date(trtsdt)
                        e = self._parse_date(trtedt)
                        if s and e:
                            day = (e - s).days + 1
                            enriched['_dates'] = f"{start}/{end} ({day})"
                        else:
                            enriched['_dates'] = f"{start}/{end}"
                    except:
                        enriched['_dates'] = f"{start}/{end}"
                else:
                    enriched['_dates'] = f"{start}/{end}"
            elif src == '_duration':
                # Treatment duration in days
                trtsdt = row.get('TRTSDT', row.get('Treatment Start Date', ''))
                trtedt = row.get('TRTEDT', row.get('Treatment End Date', ''))
                if trtsdt and trtedt:
                    try:
                        from datetime import datetime
                        s = self._parse_date(trtsdt)
                        e = self._parse_date(trtedt)
                        if s and e:
                            duration = (e - s).days + 1
                            enriched['_duration'] = str(duration)
                        else:
                            enriched['_duration'] = ''
                    except:
                        enriched['_duration'] = ''
                else:
                    enriched['_duration'] = ''
            elif src == '_status':
                # Map EOSSTN to status description
                eosstn = str(row.get('EOSSTN', row.get('EOSSTT', '')))
                status_map = {
                    '1': 'Completed',
                    '2': 'Withdrawn',
                    '3': 'Lost to Follow-up',
                    '4': 'Death',
                }
                enriched['_status'] = status_map.get(eosstn, eosstn)
            elif src == '_study_duration':
                # Study duration = last dose date - first dose date (same as treatment duration for this listing)
                trtsdt = row.get('TRTSDT', row.get('Treatment Start Date', ''))
                trtedt = row.get('TRTEDT', row.get('Treatment End Date', ''))
                if trtsdt and trtedt:
                    try:
                        from datetime import datetime
                        s = self._parse_date(trtsdt)
                        e = self._parse_date(trtedt)
                        if s and e:
                            duration = (e - s).days + 1
                            enriched['_study_duration'] = str(duration)
                        else:
                            enriched['_study_duration'] = ''
                    except:
                        enriched['_study_duration'] = ''
                else:
                    enriched['_study_duration'] = ''
            elif src == '_discon':
                # Map ACTARMFL or discontinuation flag
                # Use DCTRF or other discontinuation variable
                discon_fl = row.get('DCTRF', row.get('_discon', ''))
                if discon_fl in ['Y', 'Yes', '1']:
                    enriched['_discon'] = 'Yes'
                else:
                    enriched['_discon'] = 'No'

        return enriched

    def _format_date(self, val) -> str:
        """Format a date value for display."""
        if not val or str(val).strip() == '':
            return ''
        try:
            dt = self._parse_date(val)
            if dt:
                return dt.strftime('%Y-%m-%d')
        except:
            pass
        return str(val)

    def _parse_date(self, val):
        """Parse a date value, handling various formats."""
        from datetime import datetime
        if not val or str(val).strip() == '':
            return None
        val = str(val).strip()
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y%m%d']:
            try:
                return datetime.strptime(val, fmt)
            except:
                pass
        # Try pandas timestamp
        try:
            ts = pd.Timestamp(val)
            return ts.to_pydatetime()
        except:
            return None

    def _calculate_col_widths_from_defs(self, col_defs: List[Dict],
                                         data: List[Dict],
                                         available: float) -> List[float]:
        """Calculate column widths from column definitions."""
        widths = []
        for col in col_defs:
            src = col['source']
            col_name = col['name']
            base_width = col.get('width', 25)

            # Sample data for width calculation
            max_len = len(col_name.replace('\n', ' '))
            for row in data[:30]:
                if src.startswith('_'):
                    val = str(row.get(src, ''))
                else:
                    val = str(row.get(src, '')) if row.get(src) is not None else ''
                for line in val.split('\n'):
                    max_len = max(max_len, len(line))

            # Width: ~1.9mm per char at 7pt Helvetica
            ideal = max(max_len * 1.9, base_width)
            widths.append(ideal)

        # Scale proportionally if needed
        total = sum(widths)
        if total > available:
            scale = available / total
            widths = [max(w * scale, 12) for w in widths]

        # Adjust last column to fill exactly
        diff = available - sum(widths)
        if diff != 0 and widths:
            widths[-1] += diff

        return widths

    def _group_data_by(self, data: List[Dict], group_by_col: str,
                       col_defs: List[Dict]) -> List:
        """Group data by a source column name."""
        # Find the actual source column for group_by
        group_src = None
        for col in col_defs:
            if col['name'] == group_by_col or col['source'] == group_by_col:
                group_src = col['source']
                break
        if group_src is None:
            group_src = group_by_col

        groups = {}
        for row in data:
            # Try both the original group_by name and the source
            key = row.get(group_by_col) or row.get(group_src, 'Unknown')
            key = str(key) if key else 'Unknown'
            if key not in groups:
                groups[key] = []
            groups[key].append(row)

        # Sort groups
        sorted_groups = sorted(groups.items(), key=lambda x: str(x[0]))
        return sorted_groups

    def _calculate_col_widths(self, col_keys: List[str], data: List[Dict],
                              col_mapping: Dict, available: float) -> List[float]:
        """Calculate column widths - use proportional scaling only when needed."""
        sampled = data[:30] if data else []

        # First calculate ideal widths based on content
        widths = []
        for col_key in col_keys:
            max_len = len(col_key.replace('\n', ' '))
            for row in sampled:
                col_val = col_mapping[col_key]
                if callable(col_val):
                    val = str(col_val(row))
                else:
                    val = str(row.get(col_val, '')) if row.get(col_val) is not None else ''
                max_len = max(max_len, len(val))
            # Width per char at 7pt = ~2mm
            width = max_len * 2.0
            widths.append(width)

        # Only scale if absolutely necessary
        total = sum(widths)
        if total > available:
            # Scale proportionally, but keep minimum readable width
            scale = available / total
            widths = [max(w * scale, 15) for w in widths]

        # Adjust last column to fill exactly
        diff = available - sum(widths)
        if diff != 0 and widths:
            widths[-1] += diff

        return widths

    def _group_data(self, data: List[Dict], group_by: str,
                    col_keys: List[str], col_mapping: Dict) -> List:
        """Group data by a column."""
        groups = {}
        for row in data:
            key = row.get(group_by, 'Unknown')
            if key not in groups:
                groups[key] = []
            groups[key].append(row)

        # Sort groups
        sorted_groups = sorted(groups.items(), key=lambda x: str(x[0]))
        return sorted_groups

        # Calculate ideal widths
        widths = []
        for h in header:
            # Start with header length
            max_len = len(h)

            # Check data content
            for row in sampled:
                val = str(row.get(h, '')) if row.get(h) is not None else ''
                for line in val.split('\n'):
                    max_len = max(max_len, len(line))

            # Convert to mm (approx 2mm per char at 7pt)
            width = max(max_len * 1.8, 12)
            widths.append(width)

        # Scale to fit
        total = sum(widths)
        if total > available:
            scale = available / total
            widths = [max(w * scale, 10) for w in widths]

        # Ensure total fits
        diff = available - sum(widths)
        if diff != 0 and widths:
            widths[-1] += diff

        return widths


class ListingOutputGenerator:
    """Formats listing data for various output formats."""

    def generate_csv(self, listing_data: Dict[str, Any], output_path: str):
        """Generate CSV listing output."""
        if not listing_data['data']:
            df = pd.DataFrame(columns=listing_data['header'])
            df.to_csv(output_path, index=False)
            return

        df = pd.DataFrame(listing_data['data'])
        df.to_csv(output_path, index=False)
        print(f"  CSV: {output_path}")

    def generate_rtf(self, listing_data: Dict[str, Any], output_path: str,
                     protocol: str = "xxxx-x-xxxx",
                     company: str = "Daiichi Sankyo, Inc."):
        """Generate SAS-style RTF listing."""
        rtf_gen = RTFGenerator()
        rtf_gen.generate_rtf(listing_data, output_path, protocol, company)

    def generate_pdf(self, listing_data: Dict[str, Any], output_path: str,
                     protocol: str = "xxxx-x-xxxx",
                     company: str = "Daiichi Sankyo, Inc.",
                     analysis_set: str = None):
        """Generate SAS-style PDF listing using reportlab."""
        pdf_gen = PDFListingGenerator()
        pdf_gen.generate_pdf(listing_data, output_path, protocol, company, analysis_set)

    def generate_txt(self, listing_data: Dict[str, Any], output_path: str,
                     page_width: int = 150):
        """Generate plain text listing with formatted columns (SAS-style)."""
        lines = []
        header = listing_data['header']
        data = listing_data['data']
        listing_id = listing_data.get('listing_id', '16.2.X.X')
        name = listing_data.get('name', 'Subject Listing')

        run_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Calculate column widths
        col_widths = [min(len(h), 25) for h in header]
        for row in data:
            for i, h in enumerate(header):
                val = str(row.get(h, '')) if row.get(h) is not None else ''
                col_widths[i] = max(col_widths[i], min(len(val), 30))

        # Write header
        lines.append(f"Daiichi Sankyo, Inc.                                     Listing {listing_id}.sas")
        lines.append(f"Protocol xxxx-x-xxxx                                     Run Date Time: {run_date}")
        lines.append(f"                                                                         Page 1 of 1")
        lines.append("=" * (sum(col_widths) + len(col_widths) * 2))
        lines.append(f"Listing {listing_id}: {name}")
        lines.append("-" * (sum(col_widths) + len(col_widths) * 2))

        header_line = "  ".join(h[:col_widths[i]].ljust(col_widths[i]) for i, h in enumerate(header))
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Write data rows
        for row in data:
            row_str = "  ".join(str(row.get(h, '') or '')[:col_widths[i]].ljust(col_widths[i])
                               for i, h in enumerate(header))
            lines.append(row_str)

        lines.append("=" * (sum(col_widths) + len(col_widths) * 2))

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        print(f"  TXT: {output_path}")


# ============================================================================
# Listing Generation Functions (Public API)
# ============================================================================

def generate_listing(
    listing_id: str,
    data_dir: str,
    output_dir: str,
    format: str = "csv"
) -> Dict[str, str]:
    """
    Generate a patient data listing.

    Args:
        listing_id: e.g. "16.2.7.1" for AE listing
        data_dir: Path to ADaM data directory
        output_dir: Directory to save outputs
        format: Output format ("csv", "txt", or "both")

    Returns:
        Dict with output file paths
    """
    # Create listing analyzer
    analyzer = ListingAnalyzer(data_dir)

    # Generate listing data
    print(f"Generating listing {listing_id}...")
    listing_data = analyzer.generate_listing(listing_id)

    if listing_data['message']:
        print(f"  Warning: {listing_data['message']}")

    print(f"  Found {listing_data['total_records']} records")

    # Generate outputs
    output_gen = ListingOutputGenerator()
    outputs = {}

    listing_clean = listing_id.replace('.', '_')

    # Generate CSV in csv/listing folder
    csv_path = Path(output_dir) / "csv" / "listing" / f"listing_{listing_clean}.csv"
    output_gen.generate_csv(listing_data, str(csv_path))
    outputs['csv'] = str(csv_path)

    # Generate PDF listing in report/listing folder
    pdf_base = Path(output_dir) / "report" / "listing" / f"Listing_{listing_clean}"
    pdf_path = str(pdf_base) + ".pdf"
    output_gen.generate_pdf(listing_data, pdf_path)
    outputs['pdf'] = pdf_path

    return outputs


def generate_listing_report(
    listing_id: str,
    data_dir: str,
    output_dir: str
) -> Dict[str, str]:
    """Generate listing with both CSV and TXT outputs."""
    return generate_listing(listing_id, data_dir, output_dir, format="both")
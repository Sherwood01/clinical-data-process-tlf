"""
ADaM Dataset Spec Reader - Reads CDISC ADaM variable specifications for RAG indexing.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ADaMSpecVariable:
    """Represents an ADaM dataset variable specification."""
    name: str
    type: str  # char, numeric
    label: str = ""
    core: str = ""  # Core variable indicator (Yes, No, Perm, Cond)
    origin: str = ""  # Origin (Protocol, CRF, Derived, etc.)
    comment: str = ""


@dataclass
class ADaMSpecDataset:
    """Represents an ADaM dataset specification."""
    name: str
    description: str = ""
    variables: list[ADaMSpecVariable] = field(default_factory=list)
    keys: list[str] = field(default_factory=list)  # Primary keys


class ADaMSpecReader:
    """Reader for ADaM specifications (CDISC standards) - NOT project data."""

    # Standard ADaM datasets and their variables (CDISC ADaM IG)
    STANDARD_SPECS = {
        "ADSL": {
            "description": "Subject-Level Analysis Dataset",
            "keys": ["STUDYID", "USUBJID"],
            "variables": [
                {"name": "STUDYID", "type": "char", "label": "Study Identifier", "core": "Yes"},
                {"name": "USUBJID", "type": "char", "label": "Unique Subject Identifier", "core": "Yes"},
                {"name": "SUBJID", "type": "char", "label": "Subject Identifier", "core": "Yes"},
                {"name": "SITEID", "type": "char", "label": "Site Identifier", "core": "Yes"},
                {"name": "TRT01P", "type": "char", "label": "Planned Treatment", "core": "Yes"},
                {"name": "TRT01PN", "type": "numeric", "label": "Planned Treatment (N)", "core": "Yes"},
                {"name": "TRT01A", "type": "char", "label": "Actual Treatment", "core": "Yes"},
                {"name": "TRT01AN", "type": "numeric", "label": "Actual Treatment (N)", "core": "Yes"},
                {"name": "ENRLFL", "type": "char", "label": "Enrolled Flag", "core": "Yes"},
                {"name": "SAFFL", "type": "char", "label": "Safety Analysis Flag", "core": "Yes"},
                {"name": "RANDFL", "type": "char", "label": "Randomized Flag", "core": "Yes"},
                {"name": "AGE", "type": "numeric", "label": "Age", "core": "Yes"},
                {"name": "AGEU", "type": "char", "label": "Age Units", "core": "Yes"},
                {"name": "SEX", "type": "char", "label": "Sex", "core": "Yes"},
                {"name": "RACE", "type": "char", "label": "Race", "core": "Yes"},
                {"name": "ETHNIC", "type": "char", "label": "Ethnicity", "core": "Yes"},
                {"name": "DTHFL", "type": "char", "label": "Death Flag", "core": "No"},
                {"name": "DTHDTC", "type": "char", "label": "Death Date", "core": "No"},
            ]
        },
        "ADAE": {
            "description": "Adverse Events Analysis Dataset",
            "keys": ["STUDYID", "USUBJID", "AETERM"],
            "variables": [
                {"name": "STUDYID", "type": "char", "label": "Study Identifier", "core": "Yes"},
                {"name": "USUBJID", "type": "char", "label": "Unique Subject Identifier", "core": "Yes"},
                {"name": "TRTP", "type": "char", "label": "Actual Treatment", "core": "Yes"},
                {"name": "TRTPN", "type": "numeric", "label": "Actual Treatment (N)", "core": "Yes"},
                {"name": "AETERM", "type": "char", "label": "Adverse Event Term", "core": "Yes"},
                {"name": "AEDECOD", "type": "char", "label": "Dictionary-Derived Term", "core": "Yes"},
                {"name": "AESOC", "type": "char", "label": "System Organ Class", "core": "Yes"},
                {"name": "AESTDTC", "type": "char", "label": "Start Date/Time of Adverse Event", "core": "Yes"},
                {"name": "AEENDTC", "type": "char", "label": "End Date/Time of Adverse Event", "core": "Yes"},
                {"name": "AESTDY", "type": "numeric", "label": "Study Day of Start of Adverse Event", "core": "No"},
                {"name": "TRTEMFL", "type": "char", "label": "Treatment-Emergent Adverse Event Flag", "core": "Yes"},
                {"name": "AEREL", "type": "char", "label": "Relationship to Study Treatment", "core": "No"},
                {"name": "AESER", "type": "char", "label": "Serious Adverse Event Flag", "core": "Yes"},
                {"name": "AEOUT", "type": "char", "label": "Outcome of Adverse Event", "core": "No"},
                {"name": "AETOXGR", "type": "char", "label": "Adverse Event Toxicity Grade", "core": "No"},
            ]
        },
        "ADRS": {
            "description": "Response Analysis Dataset",
            "keys": ["STUDYID", "USUBJID", "PARAM"],
            "variables": [
                {"name": "STUDYID", "type": "char", "label": "Study Identifier", "core": "Yes"},
                {"name": "USUBJID", "type": "char", "label": "Unique Subject Identifier", "core": "Yes"},
                {"name": "TRTP", "type": "char", "label": "Actual Treatment", "core": "Yes"},
                {"name": "TRTPN", "type": "numeric", "label": "Actual Treatment (N)", "core": "Yes"},
                {"name": "PARAM", "type": "char", "label": "Parameter", "core": "Yes"},
                {"name": "PARAMCD", "type": "char", "label": "Parameter Code", "core": "Yes"},
                {"name": "AVISIT", "type": "char", "label": "Analysis Visit", "core": "Yes"},
                {"name": "AVAL", "type": "numeric", "label": "Analysis Value", "core": "Yes"},
                {"name": "AVALC", "type": "char", "label": "Analysis Value (C)", "core": "Yes"},
                {"name": "ADT", "type": "numeric", "label": "Analysis Date", "core": "Yes"},
            ]
        },
        "ADTTE": {
            "description": "Time-to-Event Analysis Dataset",
            "keys": ["STUDYID", "USUBJID", "PARAM"],
            "variables": [
                {"name": "STUDYID", "type": "char", "label": "Study Identifier", "core": "Yes"},
                {"name": "USUBJID", "type": "char", "label": "Unique Subject Identifier", "core": "Yes"},
                {"name": "TRTP", "type": "char", "label": "Actual Treatment", "core": "Yes"},
                {"name": "TRTPN", "type": "numeric", "label": "Actual Treatment (N)", "core": "Yes"},
                {"name": "PARAM", "type": "char", "label": "Parameter", "core": "Yes"},
                {"name": "PARAMCD", "type": "char", "label": "Parameter Code", "core": "Yes"},
                {"name": "AVAL", "type": "numeric", "label": "Analysis Value (Time)", "core": "Yes"},
                {"name": "CNSR", "type": "numeric", "label": "Censor Flag", "core": "Yes"},
                {"name": "EVNTDESC", "type": "char", "label": "Event Description", "core": "No"},
            ]
        },
        "ADCM": {
            "description": "Concomitant Medications Analysis Dataset",
            "keys": ["STUDYID", "USUBJID", "CMTRT"],
            "variables": [
                {"name": "STUDYID", "type": "char", "label": "Study Identifier", "core": "Yes"},
                {"name": "USUBJID", "type": "char", "label": "Unique Subject Identifier", "core": "Yes"},
                {"name": "TRTP", "type": "char", "label": "Actual Treatment", "core": "Yes"},
                {"name": "CMTRT", "type": "char", "label": "Concomitant Medication Name", "core": "Yes"},
                {"name": "CMDECOD", "type": "char", "label": "Dictionary-Derived Medication", "core": "Yes"},
                {"name": "CMCAT", "type": "char", "label": "Category", "core": "No"},
                {"name": "CMSTDTC", "type": "char", "label": "Start Date", "core": "Yes"},
                {"name": "CMENDTC", "type": "char", "label": "End Date", "core": "No"},
                {"name": "PRIORFL", "type": "char", "label": "Prior Medication Flag", "core": "Yes"},
                {"name": "CONCOMFL", "type": "char", "label": "Concomitant Medication Flag", "core": "Yes"},
            ]
        },
        "ADEX": {
            "description": "Exposure Analysis Dataset",
            "keys": ["STUDYID", "USUBJID", "EXTRT"],
            "variables": [
                {"name": "STUDYID", "type": "char", "label": "Study Identifier", "core": "Yes"},
                {"name": "USUBJID", "type": "char", "label": "Unique Subject Identifier", "core": "Yes"},
                {"name": "TRTP", "type": "char", "label": "Actual Treatment", "core": "Yes"},
                {"name": "EXTRT", "type": "char", "label": "Exposure Treatment", "core": "Yes"},
                {"name": "EXDOSE", "type": "numeric", "label": "Dose", "core": "Yes"},
                {"name": "EXDOSU", "type": "char", "label": "Dose Unit", "core": "Yes"},
                {"name": "EXSTDTC", "type": "char", "label": "Start Date/Time", "core": "Yes"},
                {"name": "EXENDTC", "type": "char", "label": "End Date/Time", "core": "Yes"},
                {"name": "NUMCYCL", "type": "numeric", "label": "Number of Cycles", "core": "No"},
            ]
        },
        "ADMH": {
            "description": "Medical History Analysis Dataset",
            "keys": ["STUDYID", "USUBJID", "MHTERM"],
            "variables": [
                {"name": "STUDYID", "type": "char", "label": "Study Identifier", "core": "Yes"},
                {"name": "USUBJID", "type": "char", "label": "Unique Subject Identifier", "core": "Yes"},
                {"name": "TRTP", "type": "char", "label": "Actual Treatment", "core": "Yes"},
                {"name": "MHTERM", "type": "char", "label": "Medical History Term", "core": "Yes"},
                {"name": "MHDECOD", "type": "char", "label": "Dictionary-Derived Term", "core": "Yes"},
                {"name": "MHCAT", "type": "char", "label": "Category", "core": "No"},
                {"name": "MHBODSYS", "type": "char", "label": "Body System", "core": "No"},
                {"name": "MHSTDTC", "type": "char", "label": "Start Date", "core": "Yes"},
            ]
        },
        "ADDV": {
            "description": "Protocol Deviation Analysis Dataset",
            "keys": ["STUDYID", "USUBJID", "DVTERM"],
            "variables": [
                {"name": "STUDYID", "type": "char", "label": "Study Identifier", "core": "Yes"},
                {"name": "USUBJID", "type": "char", "label": "Unique Subject Identifier", "core": "Yes"},
                {"name": "TRTP", "type": "char", "label": "Actual Treatment", "core": "Yes"},
                {"name": "DVTERM", "type": "char", "label": "Deviation Term", "core": "Yes"},
                {"name": "DVDECOD", "type": "char", "label": "Dictionary-Derived Term", "core": "No"},
                {"name": "DVCAT", "type": "char", "label": "Category", "core": "No"},
                {"name": "DVSTDTC", "type": "char", "label": "Start Date", "core": "No"},
            ]
        },
    }

    def __init__(self, specs_dir: str = None):
        """
        Initialize ADaM Spec Reader.

        Args:
            specs_dir: Path to ADaM specifications directory. If None, uses built-in specs.
        """
        self.specs_dir = specs_dir
        self.specs: dict[str, ADaMSpecDataset] = {}

    def load_standard_specs(self) -> dict[str, ADaMSpecDataset]:
        """Load standard CDISC ADaM specifications."""
        for name, spec_data in self.STANDARD_SPECS.items():
            variables = [
                ADaMSpecVariable(
                    name=v["name"],
                    type=v["type"],
                    label=v.get("label", ""),
                    core=v.get("core", ""),
                    origin=v.get("origin", ""),
                    comment=v.get("comment", "")
                )
                for v in spec_data["variables"]
            ]

            self.specs[name] = ADaMSpecDataset(
                name=name,
                description=spec_data.get("description", ""),
                variables=variables,
                keys=spec_data.get("keys", [])
            )

        print(f"Loaded {len(self.specs)} standard ADaM dataset specs")
        return self.specs

    def load_from_directory(self, specs_dir: str) -> dict[str, ADaMSpecDataset]:
        """Load specs from a directory (JSON files)."""
        if not os.path.exists(specs_dir):
            print(f"Warning: Specs directory not found: {specs_dir}")
            return self.load_standard_specs()

        for filename in os.listdir(specs_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(specs_dir, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                # Parse and add to specs
                name = filename.replace('.json', '')
                self.specs[name] = self._dict_to_spec_dataset(name, data)

        return self.specs

    def _dict_to_spec_dataset(self, name: str, d: dict) -> ADaMSpecDataset:
        """Convert dictionary to ADaMSpecDataset."""
        variables = [
            ADaMSpecVariable(**v) for v in d.get("variables", [])
        ]
        return ADaMSpecDataset(
            name=name,
            description=d.get("description", ""),
            variables=variables,
            keys=d.get("keys", [])
        )

    def get_spec(self, dataset_name: str) -> Optional[ADaMSpecDataset]:
        """Get spec for a dataset."""
        return self.specs.get(dataset_name.upper())

    def get_variable(self, dataset_name: str, variable_name: str) -> Optional[ADaMSpecVariable]:
        """Get variable spec from a dataset."""
        spec = self.get_spec(dataset_name)
        if not spec:
            return None
        for var in spec.variables:
            if var.name.upper() == variable_name.upper():
                return var
        return None

    def find_variable_across_datasets(self, variable_name: str) -> list[dict]:
        """Find a variable across all dataset specs."""
        variable_upper = variable_name.upper()
        results = []
        for ds_name, spec in self.specs.items():
            for var in spec.variables:
                if var.name.upper() == variable_upper:
                    results.append({
                        "dataset": ds_name,
                        "variable": var.name,
                        "type": var.type,
                        "label": var.label,
                        "core": var.core
                    })
        return results

    def get_all_variables(self) -> dict[str, list[str]]:
        """Get all variables organized by dataset."""
        return {name: [v.name for v in spec.variables]
                for name, spec in self.specs.items()}

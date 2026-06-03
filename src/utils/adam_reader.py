"""
ADaM Dataset Reader - Extracts metadata from ADaM SAS datasets for RAG indexing.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


@dataclass
class ADaMVariable:
    """Represents an ADaM dataset variable."""
    name: str
    type: str  # char, numeric
    label: str = ""
    length: int = 0
    format: str = ""
    nullable: bool = True


@dataclass
class ADaMDatasetInfo:
    """Represents extracted ADaM dataset metadata."""
    name: str
    file_path: str
    record_count: int = 0
    column_count: int = 0
    variables: list[ADaMVariable] = field(default_factory=list)
    analysis_variables: list[str] = field(default_factory=list)  # Key analysis vars
    treatment_variables: list[str] = field(default_factory=list)
    subject_key: str = "USUBJID"


class ADaMReader:
    """Reader for ADaM SAS datasets to extract metadata."""

    # Common analysis variables across ADaM datasets
    COMMON_ANALYSIS_VARS = [
        'STUDYID', 'USUBJID', 'SUBJID', 'SITEID',
        'TRTP', 'TRTPN', 'TRTA', 'TRTAN',
        'TRT01P', 'TRT01PN', 'TRT01A', 'TRT01AN',
        'TRTSDTC', 'TRTSDT', 'TRTEDTC', 'TRTEDT',
        'ENRLFL', 'SAFFL', 'RESFL', 'RANDFL',
        'AGE', 'AGEU', 'AGEGR', 'AGEGRN',
        'SEX', 'SEXN', 'RACE', 'RACEN',
    ]

    # Treatment-related variable patterns
    TREATMENT_PATTERNS = [
        r'^TRT', r'^ACTARM', r'^ARM',
    ]

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.datasets: dict[str, ADaMDatasetInfo] = {}

    def read_dataset(self, filepath: str) -> ADaMDatasetInfo:
        """Read a single ADaM dataset and extract metadata."""
        filename = os.path.basename(filepath)
        dataset_name = filename.replace('.sas7bdat', '').lower()

        # Try to read with pandas (sas7bdat or csv)
        try:
            if filepath.endswith('.sas7bdat'):
                # Try sas7bdat package first, then pyarrow
                try:
                    df = pd.read_sas(filepath, format='sas7bdat')
                except:
                    df = pd.read_sas(filepath, format='xport')
            elif filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                raise ValueError(f"Unsupported file format: {filepath}")

            info = ADaMDatasetInfo(
                name=dataset_name,
                file_path=filepath,
                record_count=len(df),
                column_count=len(df.columns)
            )

            # Extract variable metadata
            for col in df.columns:
                var = ADaMVariable(
                    name=col,
                    type=str(df[col].dtype),
                    nullable=df[col].isna().any()
                )
                info.variables.append(var)

            # Identify key analysis variables
            info.analysis_variables = self._identify_analysis_vars(df.columns)
            info.treatment_variables = self._identify_treatment_vars(df.columns)

            return info

        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            # Return minimal info
            return ADaMDatasetInfo(
                name=dataset_name,
                file_path=filepath
            )

    def _identify_analysis_vars(self, columns: list[str]) -> list[str]:
        """Identify common analysis variables present in dataset."""
        cols_upper = [c.upper() for c in columns]
        return [c for c in self.COMMON_ANALYSIS_VARS if c.upper() in cols_upper]

    def _identify_treatment_vars(self, columns: list[str]) -> list[str]:
        """Identify treatment-related variables."""
        import re
        treatment_vars = []
        for col in columns:
            col_upper = col.upper()
            for pattern in self.TREATMENT_PATTERNS:
                if re.match(pattern, col_upper):
                    treatment_vars.append(col)
                    break
        return treatment_vars

    def read_all(self) -> dict[str, ADaMDatasetInfo]:
        """Read all ADaM datasets in the directory."""
        if not os.path.exists(self.data_dir):
            print(f"Warning: Directory not found: {self.data_dir}")
            return {}

        for filename in os.listdir(self.data_dir):
            if filename.endswith(('.sas7bdat', '.csv', '.xpt')):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    info = self.read_dataset(filepath)
                    self.datasets[info.name] = info
                    print(f"Read: {filename} -> {info.name} ({info.record_count} rows, {info.column_count} cols)")
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

        return self.datasets

    def get_dataset(self, name: str) -> Optional[ADaMDatasetInfo]:
        """Get dataset info by name."""
        return self.datasets.get(name.lower())

    def get_variable_info(self, dataset_name: str, variable_name: str) -> Optional[ADaMVariable]:
        """Get variable info from a specific dataset."""
        ds = self.get_dataset(dataset_name)
        if not ds:
            return None
        for var in ds.variables:
            if var.name.upper() == variable_name.upper():
                return var
        return None

    def get_all_variables(self) -> dict[str, list[str]]:
        """Get all variables organized by dataset."""
        return {name: [v.name for v in info.variables]
                for name, info in self.datasets.items()}


if __name__ == "__main__":
    # Test reader
    import sys
    if len(sys.argv) > 1:
        reader = ADaMReader(sys.argv[1])
        datasets = reader.read_all()
        print(f"\nTotal datasets read: {len(datasets)}")

        for name, info in datasets.items():
            print(f"\n{name}:")
            print(f"  Records: {info.record_count}, Columns: {info.column_count}")
            print(f"  Analysis vars: {info.analysis_variables[:5]}...")
            print(f"  Treatment vars: {info.treatment_variables}")

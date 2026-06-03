"""
ADaM Spec Index - RAG index for CDISC ADaM variable specifications (NOT project data).
"""

import json
import os
from typing import Optional
from ..utils.adam_specs import ADaMSpecReader, ADaMSpecDataset


class ADaMMetaDataIndex:
    """
    Knowledge base for ADaM dataset specifications (CDISC standards).

    Note: This indexes CDISC ADaM variable specifications, NOT project data.
    Project ADaM data should be passed at runtime, not stored in knowledge base.
    """

    def __init__(self, specs_dir: str = None):
        """
        Initialize ADaM Spec index.

        Args:
            specs_dir: Path to ADaM specifications directory.
                      If None, uses built-in CDISC standard specs.
        """
        self.specs_dir = specs_dir
        self.reader = ADaMSpecReader(specs_dir)
        self.specs: dict[str, ADaMSpecDataset] = {}
        self._index_loaded = False

    def build_index(self) -> dict[str, ADaMSpecDataset]:
        """Build the knowledge base from CDISC ADaM specifications."""
        if self.specs_dir:
            self.specs = self.reader.load_from_directory(self.specs_dir)
        else:
            self.specs = self.reader.load_standard_specs()

        self._index_loaded = True
        print(f"Total ADaM specs indexed: {len(self.specs)}")
        return self.specs

    def load_index(self, cache_path: Optional[str] = None) -> dict[str, ADaMSpecDataset]:
        """Load existing index from cache."""
        if cache_path and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                # Convert back to ADaMSpecDataset objects
                for name, d_dict in data.items():
                    self.specs[name] = self._dict_to_spec_dataset(d_dict)
                self._index_loaded = True
                print(f"Loaded {len(self.specs)} ADaM specs from cache")
                return self.specs
            except Exception as e:
                print(f"Error loading cache: {e}")

        # Build from scratch
        return self.build_index()

    def save_index(self, cache_path: str) -> None:
        """Save index to cache file."""
        data = {name: self._spec_dataset_to_dict(d) for name, d in self.specs.items()}
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Saved {len(self.specs)} ADaM specs to {cache_path}")

    def _spec_dataset_to_dict(self, spec: ADaMSpecDataset) -> dict:
        """Convert ADaMSpecDataset to dictionary for JSON serialization."""
        return {
            "name": spec.name,
            "description": spec.description,
            "keys": spec.keys,
            "variables": [
                {
                    "name": v.name,
                    "type": v.type,
                    "label": v.label,
                    "core": v.core,
                    "origin": v.origin,
                    "comment": v.comment
                }
                for v in spec.variables
            ]
        }

    def _dict_to_spec_dataset(self, d: dict) -> ADaMSpecDataset:
        """Convert dictionary back to ADaMSpecDataset."""
        from ..utils.adam_specs import ADaMSpecVariable
        return ADaMSpecDataset(
            name=d["name"],
            description=d.get("description", ""),
            keys=d.get("keys", []),
            variables=[ADaMSpecVariable(**v) for v in d.get("variables", [])]
        )

    def get_spec(self, dataset_name: str) -> Optional[ADaMSpecDataset]:
        """Get spec for a dataset."""
        return self.specs.get(dataset_name.upper())

    def get_variable(self, dataset_name: str, variable_name: str) -> Optional:
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

    def get_dataset_variables(self, dataset_name: str) -> list[str]:
        """Get all variable names for a dataset."""
        spec = self.get_spec(dataset_name)
        if not spec:
            return []
        return [v.name for v in spec.variables]

    def validate_variables(self, dataset_name: str, variables: list[str]) -> dict:
        """Validate that variables are defined in ADaM spec for a dataset."""
        spec = self.get_spec(dataset_name)
        if not spec:
            return {"valid": False, "error": f"Dataset {dataset_name} spec not found"}

        spec_vars = {v.name.upper() for v in spec.variables}
        var_names_upper = [v.upper() for v in variables]

        found = [v for v in var_names_upper if v in spec_vars]
        missing = [v for v in var_names_upper if v not in spec_vars]

        return {
            "valid": len(missing) == 0,
            "found": found,
            "missing": missing
        }

    def get_dataset_summary(self) -> dict:
        """Get summary of all indexed specs."""
        return {
            name: {
                "description": spec.description,
                "key_variables": spec.keys,
                "variable_count": len(spec.variables)
            }
            for name, spec in self.specs.items()
        }

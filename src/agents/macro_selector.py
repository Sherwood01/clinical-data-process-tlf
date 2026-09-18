"""
Macro Selector Agent - Selects appropriate macros for TLF generation.
"""

from typing import Optional


class MacroSelectorAgent:
    """Agent for selecting appropriate SAS macros based on table specifications."""

    # Mapping of analysis types to macro categories
    ANALYSIS_TO_CATEGORY = {
        "disposition": ["descriptive_statistics"],
        "demographics": ["descriptive_statistics"],
        "ae_summary": ["descriptive_statistics", "data_manipulation"],
        "efficacy": ["statistical_analysis"],
        "survival": ["statistical_analysis"],
        "response": ["statistical_analysis"],
        "laboratory": ["descriptive_statistics"],
        "exposure": ["descriptive_statistics"],
        "conmed": ["descriptive_statistics"],
    }

    # Core macros needed for most tables
    CORE_MACROS = ["count_big_n", "freq"]

    # AE-specific macros
    AE_MACROS = ["aesum", "freq"]

    # Survival-specific macros
    SURVIVAL_MACROS = ["lifetest", "phreg", "Plot_lifetest"]

    def __init__(self, rag_retriever):
        self.rag = rag_retriever

    def select_macros_for_table(
        self,
        table_id: str,
        analysis_type: str,
        dataset_name: str,
        spec: dict
    ) -> list[dict]:
        """
        Select appropriate macros for generating a TLF table.

        Args:
            table_id: Table identifier (e.g., "14.1.1.1")
            analysis_type: Type of analysis (e.g., "disposition", "demographics")
            dataset_name: ADaM dataset to use (e.g., "adsl", "adae")
            spec: Table specification from SAP parser

        Returns:
            List of macro recommendations with parameters
        """
        results = []

        # Always need count_big_n for big N calculation
        big_n_info = self.rag.get_macro_info("count_big_n")
        if big_n_info:
            results.append({
                "macro_name": "count_big_n",
                "purpose": "Calculate denominator (big N) by treatment group",
                "parameters": {
                    "inds": dataset_name,
                    "filter": spec.get("population_filter", ""),
                    "column": spec.get("group_by", "TRT01PN")
                },
                "call_order": 1,
                "required": True
            })

        # Select analysis macros based on type
        if analysis_type in ["disposition", "demographics", "ae_summary"]:
            # Frequency/count macros
            freq_info = self.rag.get_macro_info("freq")
            if freq_info:
                results.append({
                    "macro_name": "freq",
                    "purpose": freq_info.get("purpose", "Calculate frequency counts"),
                    "parameters": {
                        "inds": dataset_name,
                        "column": spec.get("group_by", "TRT01PN"),
                        "row": self._get_row_variable(analysis_type, spec),
                        "filter": spec.get("population_filter", "")
                    },
                    "call_order": 2,
                    "required": True
                })

        elif analysis_type == "survival":
            # Survival analysis macros
            lifetest_info = self.rag.get_macro_info("lifetest")
            if lifetest_info:
                results.append({
                    "macro_name": "lifetest",
                    "purpose": "Kaplan-Meier survival analysis",
                    "parameters": {
                        "inds": dataset_name,
                        "time": "AVAL",
                        "status": "CNSR",
                        "strata": spec.get("group_by", "TRT01PN")
                    },
                    "call_order": 2,
                    "required": True
                })

        elif analysis_type == "efficacy":
            # Statistical analysis macros
            mixed_info = self.rag.get_macro_info("mixed")
            if mixed_info:
                results.append({
                    "macro_name": "mixed",
                    "purpose": "Mixed model analysis for efficacy",
                    "parameters": {
                        "inds": dataset_name,
                        "model": "AVAL = TRTPN",
                        "subjid": "USUBJID"
                    },
                    "call_order": 2,
                    "required": False
                })

        # Sort by call order
        results.sort(key=lambda x: x["call_order"])
        return results

    def _get_row_variable(self, analysis_type: str, spec: dict) -> str:
        """Determine the row variable based on analysis type."""
        analysis_vars = spec.get("analysis_variables", [])

        if analysis_type == "disposition":
            # Common disposition variables
            for var in ["DTHFL", "RANDFL", "ENRLFL"]:
                if var in analysis_vars:
                    return var
            return "DSRAFL"  # Default disposition flag

        elif analysis_type == "demographics":
            # Common demographic variables
            for var in ["AGE", "SEX", "RACE"]:
                if var in analysis_vars:
                    return var
            return "AGE"

        elif analysis_type == "ae_summary":
            # AE specific row variables
            for var in ["AEDECOD", "AESOC", "AETERM"]:
                if var in analysis_vars:
                    return var
            return "AEDECOD"

        return analysis_vars[0] if analysis_vars else "PARAM"

    def build_macro_call_sequence(self, macro_selections: list[dict]) -> list[str]:
        """
        Build a sequence of macro calls for code generation.

        Args:
            macro_selections: List of macro recommendations

        Returns:
            List of macro call strings
        """
        calls = []
        for sel in macro_selections:
            macro_name = sel["macro_name"]
            params = sel["parameters"]

            # Build parameter string
            param_strs = []
            for key, value in params.items():
                if value:  # Only include non-empty values
                    if isinstance(value, str):
                        param_strs.append(f"{key}={value}")
                    else:
                        param_strs.append(f"{key}={value}")

            param_str = ", ".join(param_strs)
            call = f"%{macro_name}({param_str})"
            calls.append(call)

        return calls

    def validate_macro_compatibility(self, macro_selections: list[dict]) -> dict:
        """
        Validate that selected macros are compatible and can work together.

        Args:
            macro_selections: List of macro selections

        Returns:
            Validation result
        """
        errors = []
        warnings = []

        # Check dependency chain
        for sel in macro_selections:
            macro_name = sel["macro_name"]
            deps = self.rag.get_macro_dependency_chain(macro_name)

            # Check if dependencies are in the selection
            selected_names = {s["macro_name"] for s in macro_selections}
            missing_deps = [d for d in deps if d not in selected_names]

            if missing_deps:
                warnings.append(f"{macro_name} depends on {missing_deps} which are not selected")

        # Check for conflicting macros
        selected_names = [s["macro_name"] for s in macro_selections]
        if "freq" in selected_names and "descriptive" in selected_names:
            warnings.append("Both freq and descriptive macros selected - may produce duplicate outputs")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

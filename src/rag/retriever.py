"""
RAG Retriever - Unified retrieval interface for macro and ADaM knowledge.
"""

from typing import Optional
from .macro_indexer import MacroKnowledgeBase
from .adam_indexer import ADaMMetaDataIndex


class RAGRetriever:
    """Unified RAG retriever for clinical data processing knowledge."""

    def __init__(
        self,
        macro_dir: str,
        adam_specs_dir: str,
        macro_cache: Optional[str] = None,
        adam_cache: Optional[str] = None
    ):
        """
        Initialize RAG retriever.

        Args:
            macro_dir: Path to SAS Macros directory (reference)
            adam_specs_dir: Path to ADaM specifications directory (reference, NOT input data)
            macro_cache: Path to macro index cache
            adam_cache: Path to ADaM spec index cache
        """
        self.macro_kb = MacroKnowledgeBase(macro_dir)
        self.adam_kb = ADaMMetaDataIndex(adam_specs_dir)  # ADaM Specs, not input data

        # Try to load from cache first
        self.macro_kb.load_index(macro_cache)
        self.adam_kb.load_index(adam_cache)

    def build_indexes(self) -> None:
        """Build both indexes from source."""
        self.macro_kb.build_index()
        self.adam_kb.build_index()

    def save_caches(self, macro_cache: str, adam_cache: str) -> None:
        """Save indexes to cache files."""
        self.macro_kb.save_index(macro_cache)
        self.adam_kb.save_index(adam_cache)

    def retrieve_macros_for_table(
        self,
        table_id: str,
        analysis_type: str,
        dataset_name: str
    ) -> list[dict]:
        """
        Retrieve macros suitable for generating a specific TLF table.

        Args:
            table_id: Table identifier (e.g., "14.1.1.1")
            analysis_type: Type of analysis (e.g., "disposition", "demographics", "ae_summary")
            dataset_name: ADaM dataset to use (e.g., "adsl", "adae")

        Returns:
            List of macro recommendations with explanations
        """
        results = []

        # Find macros by category based on analysis type
        category_map = {
            "disposition": "descriptive_statistics",
            "demographics": "descriptive_statistics",
            "ae_summary": "descriptive_statistics",
            "efficacy": "statistical_analysis",
            "survival": "statistical_analysis",
            "response": "statistical_analysis",
        }

        category = category_map.get(analysis_type.lower(), "descriptive_statistics")
        macros = self.macro_kb.get_macros_by_category(category)

        for macro in macros:
            results.append({
                "macro_name": macro.name,
                "category": macro.category,
                "purpose": macro.purpose,
                "parameters": [p.name for p in macro.parameters],
                "called_macros": macro.called_macros,
                "applicable_tables": macro.applicable_tables,
                "confidence": 0.8 if analysis_type.lower() in macro.name.lower() else 0.5
            })

        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    def retrieve_macro_by_purpose(self, purpose: str) -> list[dict]:
        """
        Find macros by describing what you want to accomplish.

        Args:
            purpose: Description like "calculate frequency with percentage"

        Returns:
            List of matching macros with relevance scores
        """
        scored = self.macro_kb.find_macros_for_task(purpose)
        return [
            {
                "macro_name": m.name,
                "category": m.category,
                "purpose": m.purpose,
                "parameters": [p.name for p in m.parameters],
                "relevance_score": score
            }
            for m, score in scored
        ]

    def validate_table_generation(
        self,
        table_id: str,
        dataset_name: str,
        required_variables: list[str]
    ) -> dict:
        """
        Validate if a table can be generated from a dataset.

        Args:
            table_id: Table identifier
            dataset_name: ADaM dataset name
            required_variables: List of required variable names

        Returns:
            Validation result with found/missing variables
        """
        validation = self.adam_kb.validate_variables(dataset_name, required_variables)
        validation["table_id"] = table_id
        validation["dataset"] = dataset_name
        return validation

    def get_dataset_info(self, dataset_name: str) -> Optional[dict]:
        """Get comprehensive info about a dataset."""
        ds = self.adam_kb.get_dataset(dataset_name)
        if not ds:
            return None

        return {
            "name": ds.name,
            "record_count": ds.record_count,
            "column_count": ds.column_count,
            "variables": [v.name for v in ds.variables],
            "analysis_variables": ds.analysis_variables,
            "treatment_variables": ds.treatment_variables,
            "subject_key": ds.subject_key
        }

    def get_macro_info(self, macro_name: str) -> Optional[dict]:
        """Get comprehensive info about a macro."""
        macro = self.macro_kb.get_macro(macro_name)
        if not macro:
            return None

        return {
            "name": macro.name,
            "file_path": macro.file_path,
            "category": macro.category,
            "purpose": macro.purpose,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "required": p.required,
                    "default": p.default
                }
                for p in macro.parameters
            ],
            "output_dataset": macro.output_dataset,
            "output_variables": macro.output_variables,
            "called_macros": macro.called_macros,
            "usage_example": self.macro_kb.get_macro_usage_example(macro_name)
        }

    def get_macro_dependency_chain(self, macro_name: str) -> list[str]:
        """Get the full dependency chain for a macro."""
        visited = set()
        chain = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            macro = self.macro_kb.get_macro(name)
            if macro:
                for dep in macro.called_macros:
                    visit(dep)
                chain.append(name)

        visit(macro_name)
        return chain

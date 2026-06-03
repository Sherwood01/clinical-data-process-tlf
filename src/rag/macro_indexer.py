"""
Macro Knowledge Base - RAG index for SAS macros.
"""

import json
import os
from typing import Optional
from ..utils.sas_parser import SASMacroParser, MacroInfo


class MacroKnowledgeBase:
    """Knowledge base for SAS macros with RAG indexing."""

    def __init__(self, macro_dir: str):
        self.macro_dir = macro_dir
        self.parser = SASMacroParser(macro_dir)
        self.macros: dict[str, MacroInfo] = {}
        self._index_loaded = False

    def build_index(self) -> dict[str, MacroInfo]:
        """Build the knowledge base by parsing all macros."""
        print(f"Building macro knowledge base from: {self.macro_dir}")
        self.macros = self.parser.parse_all()
        self._index_loaded = True
        print(f"Total macros indexed: {len(self.macros)}")
        return self.macros

    def load_index(self, cache_path: Optional[str] = None) -> dict[str, MacroInfo]:
        """Load existing index from cache."""
        if cache_path and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                # Convert back to MacroInfo objects
                for name, m_dict in data.items():
                    self.macros[name] = self._dict_to_macro_info(m_dict)
                self._index_loaded = True
                print(f"Loaded {len(self.macros)} macros from cache")
                return self.macros
            except Exception as e:
                print(f"Error loading cache: {e}")

        # Build from scratch
        return self.build_index()

    def save_index(self, cache_path: str) -> None:
        """Save index to cache file."""
        data = {name: self._macro_info_to_dict(m) for name, m in self.macros.items()}
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(self.macros)} macros to {cache_path}")

    def _macro_info_to_dict(self, info: MacroInfo) -> dict:
        """Convert MacroInfo to dictionary for JSON serialization."""
        return {
            "name": info.name,
            "file_path": info.file_path,
            "purpose": info.purpose,
            "category": info.category,
            "parameters": [
                {"name": p.name, "type": p.type, "required": p.required,
                 "description": p.description, "default": p.default}
                for p in info.parameters
            ],
            "output_dataset": info.output_dataset,
            "output_variables": info.output_variables,
            "called_macros": info.called_macros,
            "applicable_tables": info.applicable_tables,
            "code_snippet": info.code_snippet,
        }

    def _dict_to_macro_info(self, d: dict) -> MacroInfo:
        """Convert dictionary back to MacroInfo."""
        from ..utils.sas_parser import MacroParameter
        return MacroInfo(
            name=d["name"],
            file_path=d["file_path"],
            purpose=d.get("purpose", ""),
            category=d.get("category", ""),
            parameters=[MacroParameter(**p) for p in d.get("parameters", [])],
            output_dataset=d.get("output_dataset", ""),
            output_variables=d.get("output_variables", []),
            called_macros=d.get("called_macros", []),
            applicable_tables=d.get("applicable_tables", []),
            code_snippet=d.get("code_snippet", ""),
        )

    def get_macro(self, name: str) -> Optional[MacroInfo]:
        """Get macro by name."""
        return self.macros.get(name)

    def get_macros_by_category(self, category: str) -> list[MacroInfo]:
        """Get all macros in a category."""
        return self.parser.get_macros_by_category(category)

    def get_categories(self) -> list[str]:
        """Get all unique categories."""
        return list(set(m.category for m in self.macros.values()))

    def get_dependency_graph(self) -> dict[str, list[str]]:
        """Get macro dependency graph."""
        return self.parser.get_macro_dependency_graph()

    def find_macros_for_task(self, task_description: str) -> list[tuple[MacroInfo, float]]:
        """Find macros suitable for a task based on description."""
        # Simple keyword matching for now
        # In production, this would use vector similarity
        task_lower = task_description.lower()
        keywords = {
            "frequency": ["freq", "count", "discrete"],
            "descriptive": ["descriptive", "summary", "mean", "sd"],
            "statistical": ["chisq", "fisher", "mixed", "phreg", "lifetest"],
            "visualization": ["plot", "box", "forest", "swimmer"],
            "output": ["output", "report", "rtf", "table", "listing"],
            "data": ["varlist", "transpose", "merge", "sort"],
        }

        scores = []
        for macro in self.macros.values():
            score = 0.0
            for category, kws in keywords.items():
                if macro.category == category:
                    score += 2.0
                for kw in kws:
                    if kw in macro.name.lower() or kw in (macro.purpose or "").lower():
                        score += 1.0
            if score > 0:
                scores.append((macro, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def get_macro_usage_example(self, macro_name: str) -> str:
        """Get a typical usage example for a macro."""
        # Look up usage in TLF programs
        # For now, return a template
        macro = self.get_macro(macro_name)
        if not macro:
            return ""

        params = [p.name for p in macro.parameters if p.required]
        if not params:
            params = [p.name for p in macro.parameters[:3]]

        param_str = ", ".join([f"{p}=?" for p in params])
        return f"%{macro_name}({param_str})"

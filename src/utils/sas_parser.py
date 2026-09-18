"""
SAS Macro Parser - Extracts metadata from SAS macro files for RAG indexing.
"""

import re
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MacroParameter:
    """Represents a SAS macro parameter."""
    name: str
    type: str = "unknown"  # dataset, variable, string, flag
    required: bool = False
    description: str = ""
    default: Optional[str] = None


@dataclass
class MacroInfo:
    """Represents extracted SAS macro metadata."""
    name: str
    file_path: str
    purpose: str = ""
    category: str = ""  # descriptive_statistics, statistical_analysis, etc.
    parameters: list[MacroParameter] = field(default_factory=list)
    output_dataset: str = ""
    output_variables: list[str] = field(default_factory=list)
    called_macros: list[str] = field(default_factory=list)
    applicable_tables: list[str] = field(default_factory=list)
    code_snippet: str = ""  # First few lines for context
    full_code: str = ""


class SASMacroParser:
    """Parser for SAS macro files to extract metadata."""

    def __init__(self, macro_dir: str):
        self.macro_dir = macro_dir
        self.macros: dict[str, MacroInfo] = {}

    def parse_file(self, filepath: str) -> MacroInfo:
        """Parse a single SAS macro file."""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        filename = os.path.basename(filepath)
        macro_name = filename.replace('.sas', '')

        info = MacroInfo(
            name=macro_name,
            file_path=filepath,
            full_code=content,
            code_snippet=content[:500]  # First 500 chars for context
        )

        # Extract purpose from comments
        info.purpose = self._extract_purpose(content)

        # Extract parameters from %macro definition
        info.parameters = self._extract_parameters(content)

        # Extract called macros
        info.called_macros = self._extract_called_macros(content)

        # Extract output info
        info.output_dataset, info.output_variables = self._extract_output(content)

        # Categorize macro
        info.category = self._categorize_macro(info)

        return info

    def _extract_purpose(self, content: str) -> str:
        """Extract macro purpose from comments."""
        # Look for block comments at the start
        comment_patterns = [
            r'/\*.*?\*/',  # /* ... */
            r'%\*.*?;',    # %* ... ;
        ]

        for pattern in comment_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                comment = match.group()
                # Clean up comment markers
                comment = re.sub(r'^[/*%]+', '', comment).strip()
                comment = re.sub(r'[*%/]+$', '', comment).strip()
                if len(comment) > 10:
                    return comment[:200]  # Limit length
        return ""

    def _extract_parameters(self, content: str) -> list[MacroParameter]:
        """Extract parameters from %macro definition."""
        params = []

        # Match %macro macro_name(param1, param2, ...);
        macro_def = re.search(
            r'%macro\s+\w+\s*\((.*?)\)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if macro_def:
            param_str = macro_def.group(1)
            # Split by comma, handling nested parentheses
            param_names = self._split_params(param_str)

            for p in param_names:
                p = p.strip()
                if not p:
                    continue

                # Check for required indicator (no = in default value)
                required = '=' not in p

                # Extract default value
                default = None
                if '=' in p:
                    parts = p.split('=', 1)
                    p = parts[0].strip()
                    default = parts[1].strip()

                # Determine parameter type heuristically
                ptype = self._infer_param_type(p, default)

                params.append(MacroParameter(
                    name=p,
                    type=ptype,
                    required=required,
                    default=default
                ))

        return params

    def _split_params(self, param_str: str) -> list[str]:
        """Split parameter string by comma, handling parentheses."""
        params = []
        current = ""
        depth = 0

        for char in param_str:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                params.append(current)
                current = ""
                continue
            current += char

        if current.strip():
            params.append(current)
        return params

    def _infer_param_type(self, name: str, default: Optional[str]) -> str:
        """Infer parameter type from name and default value."""
        name_lower = name.lower()

        # Common suffixes that indicate type
        if name_lower.endswith(('ds', 'dataset', 'data')):
            return "dataset"
        elif name_lower.endswith(('var', 'variable', 'col', 'column', 'row')):
            return "variable"
        elif name_lower.endswith(('fl', 'flag')):
            return "flag"
        elif name_lower.endswith(('n', 'num', 'count')):
            return "numeric"
        elif name_lower.endswith(('txt', 'text', 'str', 'string')):
            return "string"

        # Check default value
        if default:
            if default.upper() in ('Y', 'N'):
                return "flag"
            elif default.isdigit():
                return "numeric"

        return "unknown"

    def _extract_called_macros(self, content: str) -> list[str]:
        """Extract macros called within the macro code."""
        # Match %macro_name patterns
        pattern = r'%(\w+)\s*\('
        matches = re.findall(pattern, content)
        # Filter out common SAS keywords
        keywords = {'if', 'then', 'else', 'do', 'end', 'put', 'let', 'global', 'local'}
        return [m for m in matches if m.lower() not in keywords]

    def _extract_output(self, content: str) -> tuple[str, list[str]]:
        """Extract output dataset and variables."""
        output_ds = ""
        output_vars = []

        # Look for data out= or output dataset
        out_patterns = [
            r'data\s+(\w+)\s*;',
            r'output\s+data\s+(\w+)',
            r'proc\s+\w+\s+data=(\w+)',
        ]

        for pattern in out_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                output_ds = match.group(1)
                break

        # Look for keep/keep= statements
        keep_pattern = r'keep\s+([^;]+)'
        keep_match = re.search(keep_pattern, content, re.IGNORECASE)
        if keep_match:
            vars_str = keep_match.group(1)
            output_vars = [v.strip() for v in vars_str.split() if v.strip()]

        return output_ds, output_vars

    def _categorize_macro(self, info: MacroInfo) -> str:
        """Categorize macro based on name and content."""
        name_lower = info.name.lower()

        if any(x in name_lower for x in ['freq', 'count', 'discrete', 'summary', 'descriptive']):
            return "descriptive_statistics"
        elif any(x in name_lower for x in ['mixed', 'chisq', 'phreg', 'lifetest', 'gail', 'genmod', 'ci', 'fisher']):
            return "statistical_analysis"
        elif any(x in name_lower for x in ['plot', 'box', 'forest', 'swimmer', 'series']):
            return "visualization"
        elif any(x in name_lower for x in ['output', 'report', 'rtf', 'listing', 'table_output']):
            return "report_output"
        elif any(x in name_lower for x in ['varlist', 'var', 'transpose', 'merge', 'sort', 'add', 'insert']):
            return "data_manipulation"
        elif any(x in name_lower for x in ['clear', 'env', 'file', 'sas2', 'replace']):
            return "utility"
        else:
            return "other"

    def parse_all(self) -> dict[str, MacroInfo]:
        """Parse all SAS macro files in the directory."""
        if not os.path.exists(self.macro_dir):
            print(f"Warning: Directory not found: {self.macro_dir}")
            return {}

        for filename in os.listdir(self.macro_dir):
            if filename.endswith('.sas'):
                filepath = os.path.join(self.macro_dir, filename)
                try:
                    info = self.parse_file(filepath)
                    self.macros[info.name] = info
                    print(f"Parsed: {filename} -> {info.name} ({info.category})")
                except Exception as e:
                    print(f"Error parsing {filename}: {e}")

        return self.macros

    def get_macro_by_name(self, name: str) -> Optional[MacroInfo]:
        """Get macro info by name."""
        return self.macros.get(name)

    def get_macros_by_category(self, category: str) -> list[MacroInfo]:
        """Get all macros in a category."""
        return [m for m in self.macros.values() if m.category == category]

    def get_macro_dependency_graph(self) -> dict[str, list[str]]:
        """Build a dependency graph of macros."""
        graph = {}
        for name, info in self.macros.items():
            graph[name] = info.called_macros
        return graph


if __name__ == "__main__":
    # Test parser
    import sys
    if len(sys.argv) > 1:
        parser = SASMacroParser(sys.argv[1])
        macros = parser.parse_all()
        print(f"\nTotal macros parsed: {len(macros)}")

        # Print categories
        categories = {}
        for m in macros.values():
            if m.category not in categories:
                categories[m.category] = []
            categories[m.category].append(m.name)

        print("\nBy category:")
        for cat, names in sorted(categories.items()):
            print(f"  {cat}: {len(names)} macros")

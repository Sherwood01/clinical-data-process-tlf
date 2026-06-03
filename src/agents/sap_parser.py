"""
SAP Parser Agent - Extracts TLF specifications from SAP documents.
"""

from typing import Optional
import re


class SAPParserAgent:
    """Agent for parsing Statistical Analysis Plan documents."""

    # Table ID patterns
    TABLE_ID_PATTERN = r'(?:Table\s+)?(\d+\.\d+\.\d+\.\d+)'
    ANALYSIS_SET_PATTERN = r'(?:analysis\s+set|population|cohort)[:\s]+(\w+)'
    VARIABLE_PATTERN = r'\b(TRT\d*[APN]|ENRLFL|SAFFL|RESFL|AGE|SEX|RACE|AE\w+|PARAM)\b'

    def __init__(self, rag_retriever=None):
        self.rag = rag_retriever

    def parse_table_spec(self, table_id: str, sap_text: str) -> dict:
        """
        Parse SAP text to extract specification for a specific table.

        Args:
            table_id: Table identifier (e.g., "14.1.1.1")
            sap_text: SAP document text

        Returns:
            Dictionary with table specification
        """
        spec = {
            "table_id": table_id,
            "table_name": "",
            "analysis_set": "",
            "population_filter": "",
            "analysis_variables": [],
            "group_by": "",
            "statistics": [],
            "notes": []
        }

        # Extract table name - look for the table ID and nearby text
        table_pattern = rf'{table_id}[^\w]+([^\n]+)'
        match = re.search(table_pattern, sap_text, re.IGNORECASE)
        if match:
            spec["table_name"] = match.group(1).strip()

        # Extract analysis set
        # Common analysis sets: Enrolled, Safety, FAS, PPS, Per-Protocol
        analysis_sets = ['Enrolled', 'Safety', 'FAS', 'Full Analysis Set',
                        'Per-Protocol', 'PPS', 'Response Evaluable']
        for aset in analysis_sets:
            if aset.lower() in sap_text.lower():
                spec["analysis_set"] = aset
                break

        # Extract population filter based on analysis set
        if spec["analysis_set"]:
            filter_map = {
                "Enrolled": "ENRLFL='Y'",
                "Safety": "SAFFL='Y'",
                "FAS": "FASFL='Y'",
                "Per-Protocol": "PPSFL='Y'",
                "Response Evaluable": "RESFL='Y'"
            }
            spec["population_filter"] = filter_map.get(spec["analysis_set"], "")

        # Extract analysis variables
        vars_found = re.findall(self.VARIABLE_PATTERN, sap_text, re.IGNORECASE)
        spec["analysis_variables"] = list(set(vars_found))

        # Determine group by variable
        if "TRT" in " ".join(vars_found):
            trt_vars = [v for v in vars_found if v.startswith("TRT")]
            if trt_vars:
                spec["group_by"] = trt_vars[0]

        # Extract statistics
        stats_found = []
        stat_keywords = ['mean', 'median', 'sd', 'min', 'max', 'n (%)', 'frequency']
        for stat in stat_keywords:
            if stat in sap_text.lower():
                stats_found.append(stat)
        spec["statistics"] = stats_found

        return spec

    def parse_sap_document(self, sap_content: str) -> list[dict]:
        """
        Parse entire SAP document and extract all table specifications.

        Args:
            sap_content: Full SAP document text

        Returns:
            List of table specifications
        """
        tables = []

        # Find all table IDs mentioned in the document
        table_ids = re.findall(self.TABLE_ID_PATTERN, sap_content)
        table_ids = list(set(table_ids))  # Remove duplicates

        for table_id in table_ids:
            spec = self.parse_table_spec(table_id, sap_content)
            tables.append(spec)

        return tables

    def infer_table_type(self, table_id: str, spec: dict) -> str:
        """
        Infer the analysis type from table ID and specification.

        Table numbering convention (CDISC):
        - 14.1.X.X: Demographics/Disposition
        - 14.2.X.X: Efficacy
        - 14.3.X.X: Safety
        - 14.4.X.X: Pharmacokinetics
        - 14.5.X.X: Immunogenicity

        Args:
            table_id: Table identifier
            spec: Parsed specification

        Returns:
            Analysis type string
        """
        parts = table_id.split('.')
        if len(parts) < 2:
            return "unknown"

        section = parts[1]

        type_map = {
            "1": "disposition_demographics",
            "2": "efficacy",
            "3": "safety",
            "4": "pharmacokinetics",
            "5": "immunogenicity"
        }

        return type_map.get(section, "unknown")

    def generate_table_spec_prompt(self, table_id: str, sap_text: str) -> str:
        """
        Generate a prompt for LLM to extract table specification.

        Args:
            table_id: Table identifier
            sap_text: SAP text snippet for the table

        Returns:
            Prompt string
        """
        return f"""Extract the specification for Table {table_id} from the following SAP text:

{sap_text[:2000]}

Please provide:
1. Table name
2. Analysis set/population
3. Analysis variables (row variables)
4. Grouping variable (column variable, usually treatment)
5. Statistical methods used
6. Any special notes or footnotes
"""

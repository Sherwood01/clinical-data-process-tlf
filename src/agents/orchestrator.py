"""
Orchestrator Agent - Main coordinator for the TLF generation workflow.
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END


class TLFGenerationState(TypedDict):
    """State managed throughout the TLF generation workflow."""
    # Input
    table_id: str  # e.g., "14.1.1.1"
    analysis_type: str  # e.g., "disposition", "demographics"
    dataset_name: str  # e.g., "adsl", "adae"

    # SAP Parsing
    sap_spec: dict  # Parsed specification from SAP

    # Macro Selection
    selected_macros: list[dict]  # List of macro recommendations
    macro_calls: list[dict]  # Planned macro calls with parameters

    # Code Generation
    generated_code: str  # Generated SAS program

    # Validation
    validation_result: dict  # Validation checks

    # Output
    output_path: Optional[str]  # Path to generated file
    error: Optional[str]  # Error message if any


class OrchestratorAgent:
    """Main orchestrator agent coordinating the TLF generation workflow."""

    def __init__(self, rag_retriever):
        self.rag = rag_retriever
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(TLFGenerationState)

        # Add nodes
        workflow.add_node("parse_sap", self._parse_sap)
        workflow.add_node("select_macros", self._select_macros)
        workflow.add_node("generate_code", self._generate_code)
        workflow.add_node("validate", self._validate)

        # Define edges
        workflow.set_entry_point("parse_sap")
        workflow.add_edge("parse_sap", "select_macros")
        workflow.add_edge("select_macros", "generate_code")
        workflow.add_edge("generate_code", "validate")
        workflow.add_edge("validate", END)

        return workflow.compile()

    def _parse_sap(self, state: TLFGenerationState) -> TLFGenerationState:
        """Parse SAP specification for the table."""
        # For now, use predefined mappings
        # In production, this would call SAPParserAgent
        table_specs = {
            "14.1.1.1": {
                "table_name": "Subject Disposition",
                "analysis_set": "Enrolled Analysis Set",
                "analysis_variables": ["ENRLFL", "RANDFL", "DTHFL"],
                "population_filter": "ENRLFL='Y'",
                "group_by": "TRT01PN",
            },
            "14.1.2.1": {
                "table_name": "Demographic and Baseline Characteristics",
                "analysis_set": "Enrolled Analysis Set",
                "analysis_variables": ["AGE", "SEX", "RACE", "ETHNIC"],
                "population_filter": "ENRLFL='Y'",
                "group_by": "TRT01PN",
            },
            "14.3.1.1": {
                "table_name": "Overall Summary of TEAE",
                "analysis_set": "Safety Analysis Set",
                "analysis_variables": ["AETERM", "AEDECOD", "AESOC", "AETOXGR"],
                "population_filter": "SAFFL='Y' and TRTEMFL='Y'",
                "group_by": "TRTPN",
            },
        }

        table_id = state["table_id"]
        if table_id in table_specs:
            state["sap_spec"] = table_specs[table_id]
        else:
            state["sap_spec"] = {
                "table_name": f"Table {table_id}",
                "analysis_set": "Analysis Set",
                "analysis_variables": [],
                "population_filter": "",
                "group_by": "TRTPN",
            }

        return state

    def _select_macros(self, state: TLFGenerationState) -> TLFGenerationState:
        """Select appropriate macros for the table."""
        table_id = state["table_id"]
        analysis_type = state["analysis_type"]
        dataset_name = state["dataset_name"]

        # Retrieve macros
        macro_recs = self.rag.retrieve_macros_for_table(
            table_id, analysis_type, dataset_name
        )

        state["selected_macros"] = macro_recs

        # Build macro call plan
        # This is a simplified version - in production, more sophisticated planning
        if analysis_type in ["disposition", "demographics"]:
            state["macro_calls"] = [
                {"macro": "count_big_n", "params": {"inds": dataset_name, "filter": state["sap_spec"]["population_filter"]}},
                {"macro": "freq", "params": {"inds": dataset_name, "column": "TRT01PN"}},
            ]
        elif analysis_type == "ae_summary":
            state["macro_calls"] = [
                {"macro": "count_big_n", "params": {"inds": dataset_name, "filter": "SAFFL='Y'"}},
                {"macro": "aesum", "params": {"inds": dataset_name, "filter": "TRTEMFL='Y'"}},
            ]
        else:
            state["macro_calls"] = [
                {"macro": "freq", "params": {"inds": dataset_name}},
            ]

        return state

    def _generate_code(self, state: TLFGenerationState) -> TLFGenerationState:
        """Generate SAS code using selected macros."""
        from datetime import datetime

        table_id = state["table_id"]
        dataset = state["dataset_name"]
        spec = state.get("sap_spec", {})
        macro_calls = state.get("macro_calls", [])

        # Use the CodeGeneratorAgent to generate proper SAS code
        code_gen = self._get_code_generator()
        code = code_gen.generate_program(
            table_id=table_id,
            table_name=spec.get("table_name", f"Table {table_id}"),
            analysis_set=spec.get("analysis_set", "Analysis Set"),
            group_by=spec.get("group_by", "TRT01PN"),
            dataset=dataset,
            macro_calls=macro_calls,
            population_filter=spec.get("population_filter", "1=1")
        )

        state["generated_code"] = code
        return state

    def _get_code_generator(self):
        """Get or create a CodeGeneratorAgent instance."""
        if not hasattr(self, '_code_generator'):
            from .code_generator import CodeGeneratorAgent
            self._code_generator = CodeGeneratorAgent(self.rag)
        return self._code_generator

    def _generate_code_placeholder(self, state: TLFGenerationState) -> TLFGenerationState:
        """Generate placeholder SAS code (legacy)."""
        table_id = state["table_id"]
        dataset = state["dataset_name"]
        spec = state.get("sap_spec", {})

        code = f"""/* Generated SAS Program for {table_id} */
%include "_setup.sas";

%let tableid = {table_id};
%let tablename = {spec.get('table_name', 'Unknown')};
%let tablepop = {spec.get('analysis_set', 'Analysis Set')};
%let datasource = {dataset};

%import;

/* Analysis code would be generated here */

%output;
"""
        state["generated_code"] = code
        return state

    def _validate(self, state: TLFGenerationState) -> TLFGenerationState:
        """Validate the generated code."""
        # Basic validation
        code = state.get("generated_code", "")

        if not code:
            state["validation_result"] = {"valid": False, "error": "No code generated"}
            return state

        # Check for basic SAS syntax
        has_endsas = "%endsas" in code or "endsas" in code
        has_data_step = "data " in code.lower()

        state["validation_result"] = {
            "valid": True,
            "has_endsas": has_endsas,
            "has_data_step": has_data_step,
            "code_length": len(code)
        }

        return state

    def generate_tlf(self, table_id: str, analysis_type: str, dataset_name: str) -> dict:
        """
        Generate a TLF SAS program.

        Args:
            table_id: Table identifier (e.g., "14.1.1.1")
            analysis_type: Type of analysis
            dataset_name: ADaM dataset name

        Returns:
            Final state with generated code
        """
        initial_state = TLFGenerationState(
            table_id=table_id,
            analysis_type=analysis_type,
            dataset_name=dataset_name,
            sap_spec={},
            selected_macros=[],
            macro_calls=[],
            generated_code="",
            validation_result={},
            output_path=None,
            error=None
        )

        result = self.graph.invoke(initial_state)
        return result


if __name__ == "__main__":
    # Test the orchestrator
    from rag import RAGRetriever

    KNOWLEDGE_DIR = ".knowledge"

    rag = RAGRetriever(
        macro_dir=f"{KNOWLEDGE_DIR}/SAS Macros",
        adam_dir=f"{KNOWLEDGE_DIR}/ADaM/data",
    )

    orchestrator = OrchestratorAgent(rag)

    result = orchestrator.generate_tlf(
        table_id="14.1.1.1",
        analysis_type="disposition",
        dataset_name="adsl"
    )

    print("Generated Code:")
    print(result.get("generated_code", ""))

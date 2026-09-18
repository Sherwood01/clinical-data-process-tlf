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

    async def _parse_sap(self, state: TLFGenerationState) -> TLFGenerationState:
        """Parse SAP specification for the table dynamically using LLM."""
        table_id = state["table_id"]
        analysis_type = state["analysis_type"]
        dataset_name = state["dataset_name"]

        # 1. 预置基准硬编码规则作为高优先级优先匹配
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

        # 1.5 优先读取用户在前端校正好的 custom_specs.json 变量规格
        import os
        import json
        custom_specs_path = "/app/knowledge/custom_specs.json"
        if not os.path.exists(custom_specs_path):
            custom_specs_path = "knowledge/custom_specs.json"
            
        if os.path.exists(custom_specs_path):
            try:
                with open(custom_specs_path, "r", encoding="utf-8") as f:
                    custom_data = json.load(f)
                if table_id in custom_data:
                    state["sap_spec"] = custom_data[table_id]
                    return state
            except Exception as e:
                print(f"Error loading custom_specs.json in orchestrator: {e}")

        if table_id in table_specs:
            state["sap_spec"] = table_specs[table_id]
            return state

        # 2. 如果是自定义的表格，调用 LLM 倒推分析元数据
        import os
        import json
        try:
            from backend.services.ai.config import deepseek_client, MODEL_NAME
            model_to_use = MODEL_NAME
        except ImportError:
            from openai import AsyncOpenAI
            deepseek_client = AsyncOpenAI(
                api_key=os.environ.get("DEEPSEEK_API_KEY", "mock-key-for-local-testing"),
                base_url="https://api.deepseek.com"
            )
            model_to_use = "deepseek-v4-flash"

        system_prompt = """你是一位精通 CDISC 与 临床试验 SAP 规范的医学数据科学家。
请根据给定的表格ID、分析类型和数据集，智能倒推合理的 SAP 规格参数，以便后续的 SAS 代码生成。

输出必须是合法的 JSON 对象，格式为：
{
  "table_name": "表格官方名称",
  "analysis_set": "分析人群名称 (例如 Safety Analysis Set)",
  "analysis_variables": ["变量名1", "变量名2"],
  "population_filter": "SAS的where过滤条件 (例如 SAFFL='Y')",
  "group_by": "分组变量 (例如 TRT01PN)"
}
不要包含任何额外的 markdown 标记或说明解释。"""

        user_prompt = f"表格ID: {table_id}\n分析类型: {analysis_type}\n数据集: {dataset_name}"

        try:
            response = await deepseek_client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                timeout=20.0
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            state["sap_spec"] = json.loads(raw.strip())
        except Exception as e:
            print(f"Error in dynamic _parse_sap: {e}")
            # Fallback
            state["sap_spec"] = {
                "table_name": f"Table {table_id}",
                "analysis_set": "Analysis Set",
                "analysis_variables": [],
                "population_filter": "",
                "group_by": "TRT01PN",
            }
        return state

    async def _select_macros(self, state: TLFGenerationState) -> TLFGenerationState:
        """Select appropriate macros for the table using AI RAG retrieval."""
        table_id = state["table_id"]
        analysis_type = state["analysis_type"]
        dataset_name = state["dataset_name"]
        table_name = state.get("sap_spec", {}).get("table_name", f"Table {table_id}")

        # 调用我们最新研发的 RAG AI 智能关联检索
        macro_recs = await self.rag.retrieve_macros_with_ai(
            table_id=table_id,
            table_name=table_name,
            analysis_type=analysis_type,
            dataset_name=dataset_name
        )

        state["selected_macros"] = macro_recs

        # 构建大模型推荐的宏调用指令参数列表
        macro_calls = []
        for rec in macro_recs:
            if rec.get("confidence", 0) > 0.6:
                macro_calls.append({
                    "macro": rec.get("macro_name"),
                    "params": rec.get("parameter_mappings", {})
                })
        
        # 如果大模型匹配返回空，降级为常规规则匹配
        if not macro_calls:
            if analysis_type in ["disposition", "demographics"]:
                macro_calls = [
                    {"macro": "count_big_n", "params": {"inds": dataset_name, "filter": state["sap_spec"]["population_filter"]}},
                    {"macro": "freq", "params": {"inds": dataset_name, "column": "TRT01PN"}},
                ]
            else:
                macro_calls = [
                    {"macro": "freq", "params": {"inds": dataset_name}},
                ]

        state["macro_calls"] = macro_calls
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

    async def generate_tlf(self, table_id: str, analysis_type: str, dataset_name: str) -> dict:
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

        result = await self.graph.ainvoke(initial_state)
        return result


if __name__ == "__main__":
    # Test the orchestrator
    from rag import RAGRetriever

    KNOWLEDGE_DIR = ".knowledge"

    rag = RAGRetriever(
        macro_dir=f"{KNOWLEDGE_DIR}/SAS Macros",
        adam_dir=f"{KNOWLEDGE_DIR}/ADaM/data",
    )

    import asyncio
    orchestrator = OrchestratorAgent(rag)

    result = asyncio.run(orchestrator.generate_tlf(
        table_id="14.1.1.1",
        analysis_type="disposition",
        dataset_name="adsl"
    ))

    print("Generated Code:")
    print(result.get("generated_code", ""))

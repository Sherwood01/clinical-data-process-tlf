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
        Enhanced to perform multi-stage relevance checking on applicable_tables and purposes.
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
            confidence = 0.5
            
            # 1. Check applicable tables (e.g. ['14.1.1', '14.1.2'])
            if macro.applicable_tables:
                for app_t in macro.applicable_tables:
                    if app_t == table_id or table_id.startswith(app_t):
                        confidence = 0.95
                        break
            
            # 2. Check keyword overlap
            if analysis_type.lower() in macro.name.lower():
                confidence = max(confidence, 0.8)
            if macro.purpose and analysis_type.lower() in macro.purpose.lower():
                confidence = max(confidence, 0.7)

            results.append({
                "macro_name": macro.name,
                "category": macro.category,
                "purpose": macro.purpose,
                "parameters": [p.name for p in macro.parameters],
                "called_macros": macro.called_macros,
                "applicable_tables": macro.applicable_tables,
                "confidence": confidence
            })

        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    async def retrieve_macros_with_ai(
        self,
        table_id: str,
        table_name: str,
        analysis_type: str,
        dataset_name: str
    ) -> list[dict]:
        """
        Use LLM to retrieve and align macros from the knowledge base for a specific table design.
        Includes automatic fallback to local heuristic matching in case of network errors.
        """
        import os
        import json
        
        # 1. Dynamically import configured deepseek client
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

        # 2. Extract context from all registered macros
        candidates = []
        for name, macro in self.macro_kb.macros.items():
            candidates.append({
                "name": name,
                "purpose": macro.purpose[:200] if macro.purpose else "",
                "parameters": [p.name for p in macro.parameters],
                "category": macro.category
            })

        system_prompt = """你是一位资深的临床试验统计程序员与 RAG 检索专家。
请根据给定的 TLF 表格分析任务，从候选宏列表中筛选出最适合完成该任务的一个或多个 SAS 宏，并为每个选中的宏提供参数绑定建议。

输出必须是合法的 JSON 数组，格式为：
[
  {
    "macro_name": "宏名字",
    "purpose": "宏用途",
    "parameters": ["参数名1", "参数名2"],
    "confidence": 0.95,
    "reason": "推荐该宏的理由",
    "parameter_mappings": {
      "inds": "数据集名",
      "column": "分组变量"
    }
  }
]
不要包含任何额外的 markdown 标记或说明解释。"""

        user_prompt = f"""表格ID: {table_id}
表格名称: {table_name}
分析类型: {analysis_type}
输入数据集: {dataset_name}

候选宏列表：
{json.dumps(candidates[:40], ensure_ascii=False, indent=2)}
"""

        try:
            response = await deepseek_client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                timeout=30.0
            )
            raw_content = response.choices[0].message.content.strip()
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()
            return json.loads(raw_content)
        except Exception as e:
            print(f"Error in retrieve_macros_with_ai: {e}")
            # Fallback to local keyword based retrieval
            local_results = self.retrieve_macros_for_table(table_id, analysis_type, dataset_name)
            return [
                {
                    "macro_name": r["macro_name"],
                    "purpose": r["purpose"],
                    "parameters": r["parameters"],
                    "confidence": r["confidence"],
                    "reason": "Local fallback retrieval",
                    "parameter_mappings": {}
                }
                for r in local_results
            ]

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

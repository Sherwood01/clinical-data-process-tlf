import os
import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/knowledge")

# 本地知识库的物理路径
KNOWLEDGE_DIR = "/app/knowledge"
MACROS_JSON = os.path.join(KNOWLEDGE_DIR, "macros.json")
CUSTOM_SPECS_JSON = os.path.join(KNOWLEDGE_DIR, "custom_specs.json")

class SpecUpdateSchema(BaseModel):
    table_name: str
    analysis_set: str
    analysis_variables: List[str]
    population_filter: str
    group_by: str

@router.get("/macros")
async def list_macros():
    """List all SAS macros from the knowledge base."""
    if not os.path.exists(MACROS_JSON):
        # 兼容开发环境本地路径
        dev_macros_json = "knowledge/macros.json"
        if os.path.exists(dev_macros_json):
            with open(dev_macros_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            return []
    else:
        try:
            with open(MACROS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to read macros: {exc}")
            
    # 将其转化为列表返回
    results = []
    for name, info in data.items():
        results.append({
            "name": name,
            "purpose": info.get("purpose", ""),
            "category": info.get("category", "descriptive_statistics"),
            "parameters": [p.get("name") if isinstance(p, dict) else p for p in info.get("parameters", [])],
            "called_macros": info.get("called_macros", []),
            "applicable_tables": info.get("applicable_tables", []),
        })
    return results

@router.post("/macros/upload")
async def upload_macro(file: UploadFile = File(...)):
    """Upload a new SAS macro, extract its definition using LLM, and merge into macros.json."""
    if not file.filename.endswith(".sas"):
        raise HTTPException(status_code=400, detail="Only .sas macro files are supported")
        
    content = await file.read()
    macro_code = content.decode("utf-8", errors="ignore")
    macro_name = os.path.splitext(file.filename)[0]

    # 使用全局 AI 客户端进行智能分析与参数提取
    from backend.services.ai.config import deepseek_client as ai_client, MODEL_NAME
    client = ai_client

    system_prompt = """You are an expert system analyzer for clinical trial SAS macros.
Please analyze the provided SAS macro source code and extract its structured attributes.

Output must be a valid JSON object matching the schema:
{
  "purpose": "A brief English sentence explaining what the macro does",
  "category": "Must be either 'descriptive_statistics' or 'statistical_analysis'",
  "parameters": [
    {
      "name": "Parameter name",
      "type": "required or optional",
      "default": "Default value (leave empty string if none)"
    }
  ],
  "called_macros": ["List of sub-macro names called by this macro"],
  "applicable_tables": ["List of table number prefixes this macro applies to, e.g. '14.1', '14.2'. Empty if none"]
}
Do not include any extra explanations or markdown formatting."""

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"SAS 宏源码名: {macro_name}\n\n代码内容：\n{macro_code}"}
            ],
            temperature=0.1,
            timeout=30.0
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        macro_meta = json.loads(raw.strip())
    except Exception as e:
        print(f"Failed to parse macro with LLM: {e}")
        # Fallback 默认解析
        macro_meta = {
            "purpose": f"Uploaded SAS Macro: {macro_name}",
            "category": "descriptive_statistics",
            "parameters": [{"name": "inds", "type": "required", "default": ""}],
            "called_macros": [],
            "applicable_tables": []
        }

    # 写入 macros.json
    try:
        data = {}
        target_path = MACROS_JSON
        if not os.path.exists(target_path):
            target_path = "knowledge/macros.json"
            
        if os.path.exists(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        data[macro_name] = {
            "name": macro_name,
            "file_path": f"SAS Macros/{file.filename}",
            "purpose": macro_meta.get("purpose", ""),
            "category": macro_meta.get("category", "descriptive_statistics"),
            "parameters": macro_meta.get("parameters", []),
            "output_dataset": "",
            "output_variables": [],
            "called_macros": macro_meta.get("called_macros", []),
            "applicable_tables": macro_meta.get("applicable_tables", []),
            "code_snippet": f"%{macro_name}(...);"
        }

        # 确保创建上级目录
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return {"status": "success", "macro_name": macro_name}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to merge macro: {exc}")

@router.get("/specs")
async def list_specs():
    """List all custom tuned variable specs."""
    target_path = CUSTOM_SPECS_JSON
    if not os.path.exists(target_path):
        target_path = "knowledge/custom_specs.json"
        
    if not os.path.exists(target_path):
        # 默认回填一些初始模板（例如 14.4.1.1 实验室表）供前端调节展示
        initial_specs = {
            "14.4.1.1": {
                "table_name": "Summary of Laboratory Parameters - Hematology",
                "analysis_set": "Safety Analysis Set",
                "analysis_variables": ["AVAL", "CHG"],
                "population_filter": "SAFFL='Y'",
                "group_by": "TRTA"
            }
        }
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(initial_specs, f, indent=2, ensure_ascii=False)
        return initial_specs
        
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read custom specs: {exc}")

@router.put("/specs/{table_id}")
async def update_spec(table_id: str, spec: SpecUpdateSchema):
    """Save or update variable specification for a table (Save & Learn)."""
    target_path = CUSTOM_SPECS_JSON
    if not os.path.exists(target_path):
        target_path = "knowledge/custom_specs.json"
        
    try:
        data = {}
        if os.path.exists(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        data[table_id] = {
            "table_name": spec.table_name,
            "analysis_set": spec.analysis_set,
            "analysis_variables": spec.analysis_variables,
            "population_filter": spec.population_filter,
            "group_by": spec.group_by
        }
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return {"status": "success", "table_id": table_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save custom spec: {exc}")


from fastapi import Query
from typing import Optional

DOCUMENTS_SUMMARY_JSON = os.path.join(KNOWLEDGE_DIR, "documents_summary.json")

# 获取 documents 列表
@router.get("/documents")
async def list_documents(study_id: Optional[str] = Query(None)):
    """List all reference documents. If study_id is provided, includes study-specific ones."""
    target_path = DOCUMENTS_SUMMARY_JSON
    if not os.path.exists(target_path):
        target_path = "knowledge/documents_summary.json"
        
    if not os.path.exists(target_path):
        return []
        
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        results = []
        for fname, info in data.items():
            doc_study_id = info.get("study_id")
            # 权限过滤：如果不传 study_id，仅返回全局文档；若传了，则返回全局文档以及该 study_id 的项目文档
            if doc_study_id:
                if study_id and str(doc_study_id) == str(study_id):
                    results.append(info)
            else:
                results.append(info)
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read document list: {exc}")

# 上传自定义文档
@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    study_id: Optional[str] = Form(None)
):
    """Upload a PDF/TXT reference document and run LLM summarization RAG indexing."""
    content = await file.read()
    # 转换为 UTF-8 文字片段，提取前 3500 字符用于摘要生成
    try:
        sample_text = content.decode("utf-8", errors="ignore")[:3500]
    except Exception:
        sample_text = ""
        
    filename = file.filename
    file_size = len(content)

    # 确定物理保存路径
    target_dir = KNOWLEDGE_DIR
    if not os.path.exists(target_dir):
        target_dir = "knowledge"
        
    if study_id:
        save_path = os.path.join(target_dir, "documents", "studies", study_id, filename)
    else:
        save_path = os.path.join(target_dir, "documents", "global", filename)
        
    # 保存文件
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save document file: {exc}")

    # 使用全局 AI 客户端进行智能分析与摘要生成
    from backend.services.ai.config import deepseek_client as ai_client, MODEL_NAME
    client = ai_client

    system_prompt = """You are a senior clinical trial document indexing expert.
Analyze the provided document sample (usually guidelines, SAP drafts, or protocol notes) and extract its key properties.

Output MUST be a valid JSON object matching the schema:
{
  "summary": "A brief English summary (around 100-150 words) explaining the document's core guidelines, variables, or instructions.",
  "keywords": ["List of 5 to 10 relevant keywords in lowercase for search indexing"]
}
Do not include any markdown format or additional text."""

    user_prompt = f"Filename: {filename}\nFile Size: {file_size} bytes\n\nContent Sample:\n{sample_text if sample_text else '[Binary or PDF content]'}"

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            timeout=30.0
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        meta = json.loads(raw.strip())
    except Exception as e:
        print(f"Failed to extract document summary via LLM: {e}")
        meta = {
            "summary": f"Uploaded guidance document '{filename}'. Useful for clinical data pipeline context.",
            "keywords": [filename.split(".")[0].lower(), "clinical", "guideline"]
        }

    # 合并写入 documents_summary.json
    summary_path = DOCUMENTS_SUMMARY_JSON
    if not os.path.exists(summary_path):
        summary_path = "knowledge/documents_summary.json"
        
    try:
        data = {}
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
        from datetime import datetime
        data[filename] = {
            "filename": filename,
            "study_id": study_id,
            "size": file_size,
            "summary": meta.get("summary", ""),
            "keywords": meta.get("keywords", []),
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return {"status": "success", "filename": filename}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to merge document metadata: {exc}")

# 删除文档
@router.delete("/documents/{filename}")
async def delete_document(
    filename: str,
    study_id: Optional[str] = Query(None)
):
    """Delete a reference document from both files and documents_summary.json."""
    # 确定保存路径
    target_dir = KNOWLEDGE_DIR
    if not os.path.exists(target_dir):
        target_dir = "knowledge"
        
    if study_id:
        save_path = os.path.join(target_dir, "documents", "studies", study_id, filename)
    else:
        save_path = os.path.join(target_dir, "documents", "global", filename)
        
    # 删除物理文件
    if os.path.exists(save_path):
        try:
            os.remove(save_path)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to delete physical file: {exc}")

    # 从 documents_summary.json 移除
    summary_path = DOCUMENTS_SUMMARY_JSON
    if not os.path.exists(summary_path):
        summary_path = "knowledge/documents_summary.json"
        
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if filename in data:
                del data[filename]
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to remove metadata: {exc}")
            
    return {"status": "success", "filename": filename}


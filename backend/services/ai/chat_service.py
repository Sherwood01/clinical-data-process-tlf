"""AI Chat Service orchestrator — manages session loops and tools streaming via WebSocket."""
import json
import logging
from uuid import UUID
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket
from backend.services.ai.config import deepseek_client, MODEL_NAME
from backend.services.ai.tools import AGENT_TOOLS, READONLY_AGENT_TOOLS, READONLY_TOOL_NAMES
from backend.services.ai import tool_handlers

logger = logging.getLogger("ai-chat-service")

SYSTEM_PROMPT = """You are a professional Clinical Trial TLF Report Assistant (Clinical TLF AI Agent).
You are integrated into a SaaS platform and can invoke the following tools to assist users:
1. Switch the currently active clinical study project (switch_study)
2. Query uploaded ADaM datasets in the current study (list_study_datasets)
3. Trigger the backend pipeline to generate standard T/F/L reports (generate_tlf_report)
4. Retrieve platform user manuals to answer usage questions and FAQs (query_user_manual)
5. Write Python code to generate custom charts within a safe container sandbox (create_custom_figure)

Behavioral Rules and Notes:
- When a user asks to generate a standard Table/Figure/Listing report supported by the system, look for the available TOC entry first (based on the user query or context) and then invoke `generate_tlf_report`.
- When a user asks to plot a custom or specialized chart not supported as a standard report, you must:
  - 1. Infer the compliance standards and chart plotting logic.
  - 2. Write a complete Python script that reads local SAS datasets (e.g. './adsl.sas7bdat' or 'adae.sas7bdat') using pandas, plots the chart using lifelines / matplotlib / seaborn, and **must write the final output as a PDF file to 'output.pdf' in the local workspace**.
  - 3. Invoke the `create_custom_figure` tool passing the code.
  - 4. Display the resulting download card to the user upon a successful sandbox run.
- **IMPORTANT**: Always respond to the user in **English**. Maintain a professional, polite, and helpful tone fitting a clinical statistician.
"""

def _get_system_prompt() -> str:
    """Helper method to load the SYSTEM_PROMPT instructions from the markdown file."""
    import os
    instructions_path = os.path.join(os.path.dirname(__file__), "ai_agent_instructions.md")
    if os.path.exists(instructions_path):
        try:
            with open(instructions_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    return content
        except Exception as e:
            logger.warning(f"Failed to read instructions markdown: {e}")
    return SYSTEM_PROMPT

def _sanitize_messages_for_llm(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitize and validate message sequence before sending to OpenAI/DeepSeek API.
    Ensures that:
    1. Every 'assistant' message with 'tool_calls' is followed by EXACTLY matching 'tool' responses 
       for every single tool_call_id in that assistant message.
    2. Any missing tool responses are auto-filled with dummy responses to satisfy OpenAI protocol.
    3. Orphaned 'tool' messages without a preceding assistant tool_calls are stripped.
    """
    sanitized = []
    i = 0
    n = len(messages)
    
    while i < n:
        msg = messages[i]
        role = msg.get("role")
        
        if role == "assistant" and msg.get("tool_calls"):
            tool_calls = msg.get("tool_calls", [])
            req_ids = []
            for tc in tool_calls:
                if isinstance(tc, dict):
                    req_ids.append(tc.get("id"))
                else:
                    req_ids.append(getattr(tc, "id", None))
            req_ids = [tid for tid in req_ids if tid]
            
            clean_assistant = {
                "role": "assistant",
                "content": msg.get("content") or "",
                "tool_calls": tool_calls
            }
            sanitized.append(clean_assistant)
            
            # Look ahead for matching tool messages for each tool_call_id
            i += 1
            tool_responses = {}
            while i < n and messages[i].get("role") == "tool":
                t_msg = messages[i]
                t_id = t_msg.get("tool_call_id")
                if t_id in req_ids and t_id not in tool_responses:
                    tool_responses[t_id] = t_msg
                i += 1
                
            # For all required tool_call_ids, output the matching response OR a fallback dummy
            for tid in req_ids:
                if tid in tool_responses:
                    sanitized.append(tool_responses[tid])
                else:
                    # Auto-fill missing tool response so API doesn't fail with 400
                    sanitized.append({
                        "role": "tool",
                        "tool_call_id": tid,
                        "content": json.dumps({"status": "completed"})
                    })
            continue
            
        elif role == "tool":
            # Orphaned tool message not consumed by assistant loop above
            i += 1
            continue
            
        elif role == "assistant":
            sanitized.append({
                "role": "assistant",
                "content": msg.get("content") or ""
            })
            i += 1
            
        else:
            sanitized.append(msg)
            i += 1
            
    return sanitized


class AIChatService:
    """Manages conversational state and runs agent execution loops for WebSocket clients."""

    def __init__(self):
        # Keeps an in-memory message history list per WebSocket connection session (OpenAI format)
        self.messages: List[Dict[str, Any]] = []

    async def chat(
        self,
        user_message: str,
        websocket: WebSocket,
        study_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        db: AsyncSession,
        mode: str = "work",
        model: str = "deepseek-v4-flash",
    ):
        """Run the main ReAct loop, streaming DeepSeek V3 response and tool call milestones back over WS."""
        # Append user message to history
        self.messages.append({"role": "user", "content": user_message})
        
        loop_count = 0
        max_loops = 5  # safety limit for tool routing recursion

        while loop_count < max_loops:
            loop_count += 1
            
            # Send status update
            await websocket.send_json({"type": "status", "status": "thinking"})
            
            # Build and sanitize messages
            raw_messages = [{"role": "system", "content": _get_system_prompt()}] + self.messages
            api_messages = _sanitize_messages_for_llm(raw_messages)
                
            # Select tool set based on mode (Work mode gets full tools; Chat mode gets read-only/QA tools)
            tools_source = AGENT_TOOLS if mode == "work" else READONLY_AGENT_TOOLS

            openai_tools = []
            for tool in tools_source:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"]
                    }
                })

            try:
                resolved_model = model
                supported_models = {"deepseek-v4-flash", "deepseek-chat", "glm-5.3-flash", "glm-4-flash", "glm-4-plus"}
                if not (
                    resolved_model.startswith("@cf/") 
                    or resolved_model.startswith("glm-") 
                    or resolved_model in supported_models
                ):
                    resolved_model = MODEL_NAME

                # 构建大模型请求参数（支持智谱 GLM、DeepSeek 及 Cloudflare Workers AI）
                create_kwargs: Dict[str, Any] = {
                    "model": resolved_model,
                    "messages": api_messages,
                    "temperature": 0.1,
                    "tools": openai_tools
                }

                # 若配置了 reasoning_effort 且模型可能支持，注入参数
                import os
                from backend.core.config import settings
                reasoning_effort = getattr(settings, "REASONING_EFFORT", None) or os.environ.get("REASONING_EFFORT")
                if reasoning_effort and (resolved_model.startswith("glm-") or "reason" in resolved_model.lower()):
                    create_kwargs["reasoning_effort"] = reasoning_effort

                try:
                    response = await deepseek_client.chat.completions.create(**create_kwargs)
                except Exception as api_err:
                    # 若因 reasoning_effort 不受支持报错，降级重试一次
                    if "reasoning_effort" in create_kwargs and "reasoning_effort" in str(api_err).lower():
                        logger.warning(f"Model {resolved_model} does not support reasoning_effort, retrying without it...")
                        del create_kwargs["reasoning_effort"]
                        response = await deepseek_client.chat.completions.create(**create_kwargs)
                    else:
                        raise api_err
            except Exception as e:
                logger.error(f"LLM API request failed: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"大模型通信失败: {str(e)}"
                })
                return

            choice = response.choices[0].message
            text_response = choice.content or ""
            tool_calls = choice.tool_calls or []

            # 1. If text response was generated, stream/send it back to client
            if text_response:
                await websocket.send_json({
                    "type": "text",
                    "content": text_response
                })

            # Format assistant message block for history
            assistant_msg = {
                "role": "assistant",
                "content": text_response or ""
            }

            if tool_calls:
                openai_tool_calls = []
                for tc in tool_calls:
                    openai_tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
                assistant_msg["tool_calls"] = openai_tool_calls

            self.messages.append(assistant_msg)

            # 2. If no tool calls requested, we are done
            if not tool_calls:
                break

            # 3. Otherwise, execute tool calls one by one
            for tc in tool_calls:
                tool_name = tc.function.name
                tool_id = tc.id
                
                # Parse arguments which are returned as a JSON string from OpenAI
                try:
                    tool_input = json.loads(tc.function.arguments)
                except Exception:
                    tool_input = {}
                
                await websocket.send_json({
                    "type": "status",
                    "status": "executing_tool",
                    "tool": tool_name
                })
                
                logger.info(f"Executing tool '{tool_name}' with input: {tool_input}")
                
                # Route and execute handler
                try:
                    if mode == "chat" and tool_name not in READONLY_TOOL_NAMES:
                        logger.info(f"Tool '{tool_name}' blocked in Chat mode. Instructing LLM to respond directly in text.")
                        res = {
                            "error": "tool_not_allowed_in_chat_mode",
                            "message": f"The action tool '{tool_name}' cannot be invoked in Chat (Read-only) mode. Please explain the answer or steps to the user directly using text."
                        }
                    elif tool_name == "switch_study":
                        res = await tool_handlers.handle_switch_study(
                            study_id=tool_input.get("study_id"),
                            tenant_id=tenant_id,
                            db=db
                        )
                    elif tool_name == "list_study_datasets":
                        res = await tool_handlers.handle_list_study_datasets(
                            study_id=study_id,
                            tenant_id=tenant_id,
                            db=db
                        )
                    elif tool_name == "generate_tlf_report":
                        res = await tool_handlers.handle_generate_tlf_report(
                            study_id=study_id,
                            toc_entry_id=tool_input.get("toc_entry_id"),
                            identifier=tool_input.get("identifier"),
                            tlf_id=tool_input.get("tlf_id"),
                            tenant_id=tenant_id,
                            user_id=user_id,
                            db=db
                        )
                    elif tool_name == "query_user_manual":
                        res = await tool_handlers.handle_query_user_manual(
                            query=tool_input.get("query"),
                            study_id=str(study_id) if study_id else None
                        )
                    elif tool_name == "create_custom_figure":
                        res = await tool_handlers.handle_create_custom_figure(
                            study_id=study_id,
                            tenant_id=tenant_id,
                            figure_title=tool_input.get("figure_title"),
                            python_code=tool_input.get("python_code"),
                            db=db
                        )
                    elif tool_name == "list_study_tocs":
                        res = await tool_handlers.handle_list_study_tocs(
                            study_id=study_id,
                            tenant_id=tenant_id,
                            db=db
                        )
                    elif tool_name == "delete_study_dataset":
                        res = await tool_handlers.handle_delete_study_dataset(
                            study_id=study_id,
                            dataset_id=tool_input.get("dataset_id"),
                            tenant_id=tenant_id,
                            db=db
                        )
                    elif tool_name == "query_billing_status":
                        res = await tool_handlers.handle_query_billing_status(
                            tenant_id=tenant_id,
                            user_id=user_id,
                            db=db
                        )
                    elif tool_name == "create_study":
                        res = await tool_handlers.handle_create_study(
                            name=tool_input.get("name"),
                            protocol_id=tool_input.get("protocol_id"),
                            description=tool_input.get("description"),
                            tenant_id=tenant_id,
                            user_id=user_id,
                            db=db
                        )
                    elif tool_name == "delete_study":
                        res = await tool_handlers.handle_delete_study(
                            target_study_id=tool_input.get("target_study_id"),
                            tenant_id=tenant_id,
                            db=db
                        )
                    elif tool_name == "delete_toc_entry":
                        res = await tool_handlers.handle_delete_toc_entry(
                            toc_entry_id=tool_input.get("toc_entry_id"),
                            tenant_id=tenant_id,
                            db=db
                        )
                    elif tool_name == "search_web":
                        res = await tool_handlers.handle_search_web(
                            query=tool_input.get("query")
                        )
                    else:
                        res = {"error": f"Unknown tool name: {tool_name}"}
                except Exception as exc:
                    logger.exception(f"Tool execution exception: {tool_name}")
                    res = {"error": f"Tool execution failed: {str(exc)}"}

                # If study is switched, tell frontend to update active URL context
                if tool_name == "switch_study" and res.get("success"):
                    await websocket.send_json({
                        "type": "action",
                        "action": "switch_study",
                        "study_id": res.get("study_id")
                    })
                    study_id = UUID(res.get("study_id"))

                # For sandbox code generation, push execution details and status
                if tool_name == "create_custom_figure":
                    await websocket.send_json({
                        "type": "custom_figure_result",
                        "success": res.get("success", False),
                        "download_url": res.get("download_url"),
                        "stdout": res.get("stdout"),
                        "error": res.get("error") or res.get("stderr")
                    })

                # Append tool result to history
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": json.dumps(res)
                })

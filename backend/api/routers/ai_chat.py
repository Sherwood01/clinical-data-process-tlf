"""WebSocket and HTTP router for interactive, database-backed AI Agent chat history."""
import json
import logging
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from backend.db.session import get_db
from backend.db.models import Study, AIChatSession, AIChatMessage
from backend.api.routers.studies import get_tenant_id, get_user_id
from backend.services.ai.chat_service import AIChatService

router = APIRouter(prefix="/ai/chat", tags=["AI Agent"])
logger = logging.getLogger("ai-chat-router")


class SessionCreateRequest(BaseModel):
    study_id: UUID
    title: str = "New Chat"


class SessionRenameRequest(BaseModel):
    title: str


@router.get("/sessions")
async def list_chat_sessions(
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve up to 10 most recent chat sessions globally for the logged-in user."""
    result = await db.execute(
        select(AIChatSession, Study.name)
        .join(Study, AIChatSession.study_id == Study.id)
        .where(
            AIChatSession.tenant_id == tenant_id,
            AIChatSession.user_id == user_id
        )
        .order_by(AIChatSession.updated_at.desc())
        .limit(10)
    )
    rows = result.all()
    return [
        {
            "id": str(row[0].id),
            "title": row[0].title,
            "study_id": str(row[0].study_id),
            "study_name": row[1],
            "updated_at": int(row[0].updated_at.timestamp() * 1000)
        }
        for row in rows
    ]


@router.post("/sessions")
async def create_chat_session(
    req: SessionCreateRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session database record and seed it with the default welcome card."""
    new_session = AIChatSession(
        study_id=req.study_id,
        tenant_id=tenant_id,
        user_id=user_id,
        title=req.title
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Pre-seed default assistant welcome message
    welcome_msg = AIChatMessage(
        session_id=new_session.id,
        role="assistant",
        content=(
            "Hello! I am your Clinical TLF AI Agent. Here is what I can assist you with:\n\n"
            "1. 🤖 **Generate Reports**: Run a standard Table, Figure, or Listing (e.g., 'Generate Table 14.1.1.1').\n"
            "2. 📚 **Q&A**: Answer platform questions or explain guidelines (e.g., 'How do I upload ADaM datasets?').\n"
            "3. 📊 **Custom Figures**: Write and run sandboxed Python scripts to generate custom clinical charts (e.g., 'Draw a KM OS survival curve').\n\n"
            "How can I help you today?"
        )
    )
    db.add(welcome_msg)
    await db.commit()
    
    return {
        "id": str(new_session.id),
        "title": new_session.title,
        "study_id": str(new_session.study_id),
        "updated_at": int(new_session.updated_at.timestamp() * 1000)
    }


@router.put("/sessions/{session_id}")
async def rename_chat_session(
    session_id: UUID,
    req: SessionRenameRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Rename the title of an existing chat session."""
    result = await db.execute(
        select(AIChatSession).where(
            AIChatSession.id == session_id,
            AIChatSession.tenant_id == tenant_id,
            AIChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.title = req.title
    session.updated_at = datetime.utcnow()
    await db.commit()
    return {"success": True}


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a chat session record (cascades and deletes all messages)."""
    result = await db.execute(
        select(AIChatSession).where(
            AIChatSession.id == session_id,
            AIChatSession.tenant_id == tenant_id,
            AIChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()
    return {"success": True}


@router.get("/sessions/{session_id}/messages")
async def list_session_messages(
    session_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Load the full messages list history for a chat session from DB."""
    session_res = await db.execute(
        select(AIChatSession).where(
            AIChatSession.id == session_id,
            AIChatSession.tenant_id == tenant_id,
            AIChatSession.user_id == user_id
        )
    )
    if not session_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    msg_res = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.session_id == session_id)
        .order_by(AIChatMessage.created_at.asc())
    )
    messages = msg_res.scalars().all()
    
    return [
        {
            "role": m.role,
            "content": m.content,
            "customFigure": m.custom_figure if m.custom_figure else None
        }
        for m in messages
        if m.role in ("user", "assistant")  # only return user and assistant to clean up front-end view
    ]


@router.websocket("/ws")
async def ai_chat_websocket(
    websocket: WebSocket,
    study_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket handler for database-backed multi-session AI Agent dialog."""
    await websocket.accept()

    try:
        study_uuid = UUID(study_id)
    except ValueError:
        await websocket.send_json({"type": "error", "message": "Invalid study ID format."})
        await websocket.close(code=4000)
        return

    # 1. Read initial auth & session frame
    try:
        first_msg = await websocket.receive_text()
        auth_data = json.loads(first_msg)
        if auth_data.get("type") != "auth":
            await websocket.send_json({"type": "error", "message": "First message must be an auth frame."})
            await websocket.close(code=4001)
            return

        tenant_id_str = auth_data.get("tenant_id")
        user_id_str = auth_data.get("user_id")
        session_id_str = auth_data.get("session_id")

        if not tenant_id_str or not user_id_str or not session_id_str:
            await websocket.send_json({"type": "error", "message": "Missing authentication credentials."})
            await websocket.close(code=4002)
            return

        tenant_uuid = UUID(tenant_id_str)
        user_uuid = UUID(user_id_str)
        session_uuid = UUID(session_id_str)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Credentials validation failed: {str(e)}"})
        await websocket.close(code=4003)
        return

    # 2. Database validation: verify tenant owns the study
    result = await db.execute(
        select(Study).where(Study.id == study_uuid, Study.tenant_id == tenant_uuid)
    )
    study = result.scalar_one_or_none()
    if not study:
        await websocket.send_json({"type": "error", "message": "Access denied: Study not found."})
        await websocket.close(code=4004)
        return

    # Verify session belongs to user
    session_res = await db.execute(
        select(AIChatSession).where(
            AIChatSession.id == session_uuid,
            AIChatSession.study_id == study_uuid,
            AIChatSession.tenant_id == tenant_uuid,
            AIChatSession.user_id == user_uuid
        )
    )
    session = session_res.scalar_one_or_none()
    if not session:
        await websocket.send_json({"type": "error", "message": "Chat session validation failed."})
        await websocket.close(code=4005)
        return

    # 3. Initialize AI Chat Service and pre-populate message history
    chat_service = AIChatService()
    
    # Fetch historical messages to provide conversational memory for the LLM
    history_res = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.session_id == session_uuid)
        .order_by(AIChatMessage.created_at.asc())
    )
    db_messages = history_res.scalars().all()
    for m in db_messages:
        chat_service.messages.append({
            "role": m.role,
            "content": m.content,
            "tool_call_id": m.tool_call_id
        })

    await websocket.send_json({
        "type": "status", 
        "status": "connected", 
        "message": f"Connected to Agent for study: {study.name}"
    })

    # 4. Message loop
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            if payload.get("type") == "abort":
                logger.info(f"AI Chat session {session_uuid} received user abort signal.")
                await websocket.send_json({"type": "status", "status": "idle"})
                continue

            user_msg = payload.get("message")
            if not user_msg:
                continue
            mode = payload.get("mode", "work")
            model = payload.get("model", "deepseek-v4-flash")

            # Record user message to database
            user_db_msg = AIChatMessage(
                session_id=session_uuid,
                role="user",
                content=user_msg
            )
            db.add(user_db_msg)
            await db.commit()

            # Record memory length before running ReAct loop
            prev_len = len(chat_service.messages)

            # Route chat processing to the orchestrator
            await chat_service.chat(
                user_message=user_msg,
                websocket=websocket,
                study_id=study_uuid,
                tenant_id=tenant_uuid,
                user_id=user_uuid,
                db=db,
                mode=mode,
                model=model
            )

            # Persist newly generated loop outputs (tools call steps and final responses)
            new_msgs = chat_service.messages[prev_len:]
            
            # Detect if a custom figure download payload was triggered during the tools run
            custom_fig_data = {}
            for msg in new_msgs:
                if msg.get("role") == "tool" and msg.get("content"):
                    try:
                        content_json = json.loads(msg["content"])
                        if "download_url" in content_json:
                            custom_fig_data = {
                                "success": content_json.get("success", True),
                                "downloadUrl": content_json.get("download_url"),
                                "stdout": content_json.get("stdout"),
                                "error": content_json.get("error") or content_json.get("stderr")
                            }
                    except Exception:
                        pass

            for msg in new_msgs:
                role = msg["role"]
                content = msg["content"]
                tool_call_id = msg.get("tool_call_id")
                
                # Bind custom figure card details to the assistant response block if triggered
                fig_obj = custom_fig_data if role == "assistant" and custom_fig_data else {}

                db_msg = AIChatMessage(
                    session_id=session_uuid,
                    role=role,
                    content=content or "",
                    tool_call_id=tool_call_id,
                    custom_figure=fig_obj
                )
                db.add(db_msg)

            # Keep session updated timestamp fresh
            session.updated_at = datetime.utcnow()
            await db.commit()

            # Mark conversation step finished and idle
            await websocket.send_json({"type": "status", "status": "idle"})

    except WebSocketDisconnect:
        logger.info(f"AI Chat WebSocket disconnected for study {study_id}")
    except Exception as e:
        logger.exception("Error in AI Chat WebSocket loop")
        try:
            await websocket.send_json({"type": "error", "message": f"Session error: {str(e)}"})
        except Exception:
            pass

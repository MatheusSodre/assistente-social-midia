import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.agent.social_media_agent import run_agent
from .schemas import ChatRequest

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/chat")
async def chat(data: ChatRequest, user=Depends(get_current_user)) -> dict[str, Any]:
    # Verify business ownership
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (data.business_id, user["sub"]),
            )
            business = cur.fetchone()
    if not business:
        raise HTTPException(404, "Business não encontrado")

    result = await run_agent(
        business_id=data.business_id,
        usuario_id=user["sub"],
        user_message=data.message,
    )
    return result


@router.get("/history/{business_id}")
def get_history(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, user["sub"]),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Business não encontrado")
            cur.execute(
                "SELECT messages, atualizado_em FROM agent_conversations WHERE business_id = %s",
                (business_id,),
            )
            row = cur.fetchone()

    if not row:
        return {"messages": [], "business_id": business_id}

    msgs = row["messages"]
    if isinstance(msgs, str):
        msgs = json.loads(msgs)

    # Return only user/assistant text messages (no tool internals)
    clean = []
    for m in (msgs or []):
        role = m.get("role")
        content = m.get("content")
        if role == "user" and isinstance(content, str):
            clean.append({"role": "user", "content": content})
        elif role == "assistant":
            if isinstance(content, str):
                if content.strip():
                    clean.append({"role": "assistant", "content": content})
            elif isinstance(content, list):
                text = next(
                    (b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip()),
                    None,
                )
                if text:
                    clean.append({"role": "assistant", "content": text})

    # Garante que o histórico não comece com assistant
    while clean and clean[0].get("role") != "user":
        clean.pop(0)

    return {"messages": clean, "business_id": business_id}


@router.delete("/history/{business_id}")
def clear_history(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, user["sub"]),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Business não encontrado")
            cur.execute(
                "DELETE FROM agent_conversations WHERE business_id = %s",
                (business_id,),
            )
    return {"message": "Histórico limpo", "business_id": business_id}

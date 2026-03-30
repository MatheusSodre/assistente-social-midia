import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.agency.sofia_agent import run_sofia
from .schemas import AgencyChatRequest

router = APIRouter(prefix="/api/v1/agency", tags=["agency"])


@router.post("/chat")
async def chat(data: AgencyChatRequest, user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (data.business_id, user["sub"]),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Business não encontrado")

    result = await run_sofia(
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
                "SELECT messages FROM agency_conversations WHERE business_id = %s",
                (business_id,),
            )
            row = cur.fetchone()

    if not row:
        return {"messages": [], "business_id": business_id}

    msgs = row["messages"]
    if isinstance(msgs, str):
        msgs = json.loads(msgs)

    clean = []
    for m in (msgs or []):
        role = m.get("role")
        content = m.get("content")
        if role == "user" and isinstance(content, str):
            clean.append({"role": "user", "content": content})
        elif role == "assistant" and isinstance(content, list):
            text = next((b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"), None)
            if text:
                clean.append({"role": "assistant", "content": text})

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
                "DELETE FROM agency_conversations WHERE business_id = %s",
                (business_id,),
            )
    return {"message": "Histórico limpo", "business_id": business_id}

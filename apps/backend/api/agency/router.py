import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.agency.sofia_agent import run_sofia

router = APIRouter(prefix="/api/v1/agency", tags=["agency"])


@router.post("/chat")
async def chat(
    business_id: str = Form(...),
    message: str = Form(""),
    image: Optional[UploadFile] = File(None),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, user["sub"]),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Business não encontrado")

    image_bytes: bytes | None = None
    if image and image.filename:
        image_bytes = await image.read()

    result = await run_sofia(
        business_id=business_id,
        usuario_id=user["sub"],
        user_message=message,
        image_bytes=image_bytes,
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
        elif role == "assistant":
            # content pode ser string (histórico antigo) ou lista de blocos
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
        # tool_results (role=user com lista) são ignorados — são internos do agente

    # Garante que o histórico não comece com assistant (API exige user primeiro)
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
                "DELETE FROM agency_conversations WHERE business_id = %s",
                (business_id,),
            )
    return {"message": "Histórico limpo", "business_id": business_id}

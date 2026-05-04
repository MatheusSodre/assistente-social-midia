"""
Notifications API — Gerencia preferências de notificação e envio via WhatsApp.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.whatsapp.client import send_text, notify_content_ready

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class UpdatePhoneRequest(BaseModel):
    telefone: str


@router.get("/preferences")
def get_preferences(user=Depends(get_current_user)) -> dict[str, Any]:
    """Retorna preferências de notificação do usuário."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT telefone FROM usuarios WHERE id = %s", (user["sub"],))
            row = cur.fetchone()
    phone = row.get("telefone") if row else None
    return {
        "whatsapp_enabled": bool(phone),
        "telefone": phone,
        "notify_on_content_ready": True,
        "weekly_summary": True,
    }


@router.post("/phone")
def update_phone(data: UpdatePhoneRequest, user=Depends(get_current_user)) -> dict[str, Any]:
    """Atualiza telefone do WhatsApp."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE usuarios SET telefone = %s WHERE id = %s",
                (data.telefone, user["sub"]),
            )
    return {"message": "Telefone atualizado", "telefone": data.telefone}


@router.post("/test")
async def test_notification(user=Depends(get_current_user)) -> dict[str, Any]:
    """Envia notificação de teste via WhatsApp."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT telefone FROM usuarios WHERE id = %s", (user["sub"],))
            row = cur.fetchone()
    phone = row.get("telefone") if row else None
    if not phone:
        raise HTTPException(400, "Telefone nao configurado. Atualize nas configuracoes.")
    result = await send_text(phone, "Teste de notificacao da Orbita.IA! Se voce recebeu essa mensagem, as notificacoes estao funcionando.")
    return result

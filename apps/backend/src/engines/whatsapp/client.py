"""
WhatsApp Client — Envia mensagens via Evolution API.
Suporta texto, imagem, e botões interativos.
"""
import os
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

EVOLUTION_BASE = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_KEY = os.getenv("EVOLUTION_API_KEY", "")
INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE", "orbita-ia")


def _headers() -> dict:
    return {
        "apikey": EVOLUTION_KEY,
        "Content-Type": "application/json",
    }


async def send_text(phone: str, message: str) -> dict[str, Any]:
    """Envia mensagem de texto via WhatsApp."""
    if not EVOLUTION_KEY:
        logger.warning("EVOLUTION_API_KEY nao configurada — WhatsApp desabilitado")
        return {"sent": False, "reason": "not_configured"}

    async with httpx.AsyncClient(timeout=15) as http:
        r = await http.post(
            f"{EVOLUTION_BASE}/message/sendText/{INSTANCE_NAME}",
            headers=_headers(),
            json={
                "number": _normalize_phone(phone),
                "textMessage": {"text": message},
            },
        )
        r.raise_for_status()
        logger.info({"event": "whatsapp_sent", "phone": phone[:8] + "..."})
        return {"sent": True, "data": r.json()}


async def send_image(phone: str, image_url: str, caption: str = "") -> dict[str, Any]:
    """Envia imagem com legenda via WhatsApp."""
    if not EVOLUTION_KEY:
        return {"sent": False, "reason": "not_configured"}

    async with httpx.AsyncClient(timeout=15) as http:
        r = await http.post(
            f"{EVOLUTION_BASE}/message/sendMedia/{INSTANCE_NAME}",
            headers=_headers(),
            json={
                "number": _normalize_phone(phone),
                "mediaMessage": {
                    "mediatype": "image",
                    "media": image_url,
                    "caption": caption,
                },
            },
        )
        r.raise_for_status()
        return {"sent": True, "data": r.json()}


async def send_buttons(phone: str, message: str, buttons: list[dict]) -> dict[str, Any]:
    """Envia mensagem com botões interativos."""
    if not EVOLUTION_KEY:
        return {"sent": False, "reason": "not_configured"}

    async with httpx.AsyncClient(timeout=15) as http:
        r = await http.post(
            f"{EVOLUTION_BASE}/message/sendButtons/{INSTANCE_NAME}",
            headers=_headers(),
            json={
                "number": _normalize_phone(phone),
                "buttonMessage": {
                    "title": "Orbita.IA",
                    "description": message,
                    "buttons": buttons,
                },
            },
        )
        r.raise_for_status()
        return {"sent": True, "data": r.json()}


async def notify_content_ready(phone: str, business_name: str, draft_count: int = 1) -> dict:
    """Notifica que conteúdo está pronto para aprovação."""
    msg = (
        f"*Orbita.IA* — Conteudo pronto!\n\n"
        f"{'Foram criados' if draft_count > 1 else 'Foi criado'} "
        f"*{draft_count} {'posts' if draft_count > 1 else 'post'}* "
        f"para *{business_name}*.\n\n"
        f"Acesse o painel para revisar e aprovar.\n"
        f"https://app.orbita.ia/dashboard"
    )
    return await send_text(phone, msg)


async def send_weekly_summary(phone: str, business_name: str, stats: dict) -> dict:
    """Envia resumo semanal de performance."""
    msg = (
        f"*Orbita.IA* — Resumo Semanal\n\n"
        f"*{business_name}*\n"
        f"Posts criados: {stats.get('created', 0)}\n"
        f"Posts publicados: {stats.get('published', 0)}\n"
        f"Total likes: {stats.get('likes', 0)}\n"
        f"Total comments: {stats.get('comments', 0)}\n"
        f"Engajamento medio: {stats.get('engagement', '0.0')}%\n\n"
        f"Continue criando conteudo incrivel!"
    )
    return await send_text(phone, msg)


def _normalize_phone(phone: str) -> str:
    """Normaliza número de telefone para formato internacional."""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone.startswith("+"):
        phone = phone[1:]
    if not phone.startswith("55"):
        phone = "55" + phone
    return phone

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.publisher.instagram import publish_image_post
from src.engines.publisher.token_manager import decrypt_token
from .schemas import SchedulePostRequest

router = APIRouter(prefix="/api/v1/schedule", tags=["schedule"])


@router.get("/calendar")
def calendar(user=Depends(get_current_user), month: int = None, year: int = None) -> list[dict[str, Any]]:
    now = datetime.utcnow()
    m = month or now.month
    y = year or now.year

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sp.id, sp.content_draft_id, sp.platform,
                       sp.scheduled_for, sp.posted_at, sp.status,
                       cd.format, cd.caption, cd.image_url, b.name as business_name
                FROM scheduled_posts sp
                JOIN content_drafts cd ON cd.id = sp.content_draft_id
                JOIN businesses b ON b.id = cd.business_id
                WHERE b.usuario_id = %s
                  AND MONTH(sp.scheduled_for) = %s
                  AND YEAR(sp.scheduled_for) = %s
                ORDER BY sp.scheduled_for
                """,
                (user["sub"], m, y),
            )
            rows = cur.fetchall()
    return rows or []


@router.post("/post")
def schedule_post(data: SchedulePostRequest, user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Verifica draft
            cur.execute(
                """
                SELECT cd.id, cd.status FROM content_drafts cd
                JOIN businesses b ON b.id = cd.business_id
                WHERE cd.id = %s AND b.usuario_id = %s
                """,
                (data.draft_id, user["sub"]),
            )
            draft = cur.fetchone()
            if not draft:
                raise HTTPException(404, "Draft não encontrado")
            if draft["status"] not in ("approved",):
                raise HTTPException(400, f"Draft deve estar aprovado para agendar (status atual: {draft['status']})")

            sp_id = str(uuid.uuid4())
            now = datetime.utcnow()
            cur.execute(
                """
                INSERT INTO scheduled_posts (id, content_draft_id, platform, scheduled_for, status, criado_em, atualizado_em)
                VALUES (%s, %s, 'instagram', %s, 'scheduled', %s, %s)
                """,
                (sp_id, data.draft_id, data.scheduled_for, now, now),
            )
            # Atualiza draft
            cur.execute(
                "UPDATE content_drafts SET scheduled_for = %s, atualizado_em = NOW() WHERE id = %s",
                (data.scheduled_for, data.draft_id),
            )
    return {"id": sp_id, "draft_id": data.draft_id, "scheduled_for": data.scheduled_for.isoformat(), "status": "scheduled"}


@router.post("/publish-now/{draft_id}")
async def publish_now(draft_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    """Publica imediatamente no Instagram."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT cd.id, cd.caption, cd.hashtags, cd.image_url, cd.status,
                       b.instagram_account_id, b.instagram_access_token
                FROM content_drafts cd
                JOIN businesses b ON b.id = cd.business_id
                WHERE cd.id = %s AND b.usuario_id = %s
                """,
                (draft_id, user["sub"]),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(404, "Draft não encontrado")
    if row["status"] not in ("approved",):
        raise HTTPException(400, "Draft deve estar aprovado para publicar")
    if not row["instagram_account_id"] or not row["instagram_access_token"]:
        raise HTTPException(400, "Instagram não conectado neste business")
    if not row["image_url"]:
        raise HTTPException(400, "Draft não possui imagem gerada")

    import json
    hashtags = json.loads(row["hashtags"]) if isinstance(row["hashtags"], str) else (row["hashtags"] or [])
    caption = row["caption"] + "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in hashtags)
    access_token = decrypt_token(row["instagram_access_token"])

    media_id = await publish_image_post(
        instagram_account_id=row["instagram_account_id"],
        access_token=access_token,
        image_url=row["image_url"],
        caption=caption,
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE content_drafts SET status = 'published', atualizado_em = NOW() WHERE id = %s",
                (draft_id,),
            )
            sp_id = str(uuid.uuid4())
            now = datetime.utcnow()
            cur.execute(
                """
                INSERT INTO scheduled_posts (id, content_draft_id, platform, scheduled_for, posted_at, instagram_media_id, status, criado_em, atualizado_em)
                VALUES (%s, %s, 'instagram', %s, %s, %s, 'published', %s, %s)
                """,
                (sp_id, draft_id, now, now, media_id, now, now),
            )

    return {"message": "Publicado com sucesso", "instagram_media_id": media_id, "status": "published"}

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.brand_context import get_unified_brand_context
from src.engines.orchestrator import generate_content
from src.engines.image_engine.imagen_client import generate_image_gemini
from src.engines.image_engine.storage import upload_image
from api.billing.router import check_can_generate, increment_post_count
from .schemas import ContentGenerateRequest, BatchGenerateRequest

router = APIRouter(prefix="/api/v1/content", tags=["content"])


@router.post("/generate")
async def generate(data: ContentGenerateRequest, user=Depends(get_current_user)) -> dict[str, Any]:
    # Verifica limites do plano
    can = check_can_generate(user["sub"], data.format)
    if not can["allowed"]:
        raise HTTPException(403, can["reason"])

    # Verifica que o business pertence ao usuário
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, type FROM businesses WHERE id = %s AND usuario_id = %s",
                (data.business_id, user["sub"]),
            )
            business = cur.fetchone()
    if not business:
        raise HTTPException(404, "Business não encontrado")

    # Load brand context for better image generation
    brand_ctx = get_unified_brand_context(data.business_id)
    strategy = brand_ctx.get("strategy", {})
    vi = brand_ctx.get("visual_identity", {})
    enriched_strategy = dict(strategy) if strategy else {}
    if vi:
        enriched_strategy["visual_identity"] = vi

    draft = await generate_content(
        business_id=data.business_id,
        business_name=business["name"],
        business_type=business["type"],
        objective=data.objective,
        format=data.format,
        tone=data.tone,
        audience=data.audience,
        brand_strategy=enriched_strategy if enriched_strategy else None,
        slide_count=data.slide_count,
    )
    increment_post_count(user["sub"])
    return draft


@router.get("/{draft_id}/preview")
def preview(draft_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT cd.* FROM content_drafts cd
                JOIN businesses b ON b.id = cd.business_id
                WHERE cd.id = %s AND b.usuario_id = %s
                """,
                (draft_id, user["sub"]),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Draft não encontrado")
    # Parse hashtags JSON
    if row.get("hashtags") and isinstance(row["hashtags"], str):
        row["hashtags"] = json.loads(row["hashtags"])
    return row


@router.post("/{draft_id}/approve")
def approve(draft_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE content_drafts cd
                JOIN businesses b ON b.id = cd.business_id
                SET cd.status = 'approved', cd.atualizado_em = NOW()
                WHERE cd.id = %s AND b.usuario_id = %s AND cd.status = 'pending_approval'
                """,
                (draft_id, user["sub"]),
            )
            if cur.rowcount == 0:
                raise HTTPException(400, "Draft não encontrado ou já processado")
    return {"message": "Conteúdo aprovado", "draft_id": draft_id, "status": "approved"}


@router.post("/{draft_id}/reject")
def reject(draft_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE content_drafts cd
                JOIN businesses b ON b.id = cd.business_id
                SET cd.status = 'rejected', cd.atualizado_em = NOW()
                WHERE cd.id = %s AND b.usuario_id = %s AND cd.status = 'pending_approval'
                """,
                (draft_id, user["sub"]),
            )
            if cur.rowcount == 0:
                raise HTTPException(400, "Draft não encontrado ou já processado")
    return {"message": "Conteúdo rejeitado", "draft_id": draft_id, "status": "rejected"}


@router.post("/{draft_id}/generate-image")
async def generate_image_for_draft(draft_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    """Gera (ou regenera) a imagem de um draft existente via Imagen."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT cd.id, cd.business_id, cd.format, cd.visual_description, cd.caption
                FROM content_drafts cd
                JOIN businesses b ON b.id = cd.business_id
                WHERE cd.id = %s AND b.usuario_id = %s
                """,
                (draft_id, user["sub"]),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(404, "Draft não encontrado")

    description = row.get("visual_description") or row.get("caption", "")
    if not description:
        raise HTTPException(400, "Draft não possui descrição visual para gerar imagem")

    brand_ctx = get_unified_brand_context(row["business_id"])
    try:
        image_bytes = await generate_image_gemini(description, row["format"], brand_context=brand_ctx)
        image_url = await upload_image(image_bytes, row["format"])
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Erro ao gerar imagem: {e}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE content_drafts SET image_url = %s, atualizado_em = NOW() WHERE id = %s",
                (image_url, draft_id),
            )

    return {"draft_id": draft_id, "image_url": image_url}


@router.post("/generate-batch")
async def generate_batch(data: BatchGenerateRequest, user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, type FROM businesses WHERE id = %s AND usuario_id = %s",
                (data.business_id, user["sub"]),
            )
            business = cur.fetchone()
    if not business:
        raise HTTPException(404, "Business não encontrado")

    tasks = [
        generate_content(
            business_id=data.business_id,
            business_name=business["name"],
            business_type=business["type"],
            objective=item.objective,
            format=item.format,
            tone=item.tone,
            audience=item.audience,
        )
        for item in data.items
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    drafts = []
    errors = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            errors.append({"index": i, "objective": data.items[i].objective, "error": str(r)})
        else:
            drafts.append(r)

    return {"created": len(drafts), "drafts": drafts, "errors": errors}


@router.get("/templates")
def get_templates(business_type: str = "", user=Depends(get_current_user)) -> list[dict]:
    """Retorna templates sugeridos para o tipo de negócio."""
    from src.engines.script_engine.templates.library import suggest_templates, TEMPLATES
    if business_type:
        return suggest_templates(business_type)
    return TEMPLATES


@router.get("")
def list_drafts(user=Depends(get_current_user), status: str = None) -> list[dict[str, Any]]:
    query = """
        SELECT cd.id, cd.business_id, b.name as business_name, cd.format,
               cd.caption, cd.hashtags, cd.image_url, cd.image_urls, cd.status,
               cd.scheduled_for, cd.criado_em
        FROM content_drafts cd
        JOIN businesses b ON b.id = cd.business_id
        WHERE b.usuario_id = %s
    """
    params = [user["sub"]]
    if status:
        query += " AND cd.status = %s"
        params.append(status)
    query += " ORDER BY cd.criado_em DESC LIMIT 50"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    for row in (rows or []):
        if row.get("hashtags") and isinstance(row["hashtags"], str):
            row["hashtags"] = json.loads(row["hashtags"])
        if row.get("image_urls") and isinstance(row["image_urls"], str):
            row["image_urls"] = json.loads(row["image_urls"])
    return rows or []

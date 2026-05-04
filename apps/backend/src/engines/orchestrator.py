import logging
import uuid
from datetime import datetime
from typing import Any

from src.db.connection import get_connection
from src.engines.brand_context import get_unified_brand_context
from src.engines.script_engine.claude_client import generate_post_script
from src.engines.image_engine.imagen_client import generate_image_gemini as generate_image
from src.engines.image_engine.storage import upload_image

logger = logging.getLogger(__name__)


async def generate_content(
    business_id: str,
    business_name: str,
    business_type: str,
    objective: str,
    format: str = "post",
    tone: str = "profissional",
    audience: str = "geral",
    brand_strategy: dict | None = None,
    slide_count: int = 5,
    uploaded_image_url: str | None = None,
) -> dict[str, Any]:
    """
    Orquestra geração completa: script → imagem(ns) → salva draft.
    Retorna o ContentDraft criado.
    """
    draft_id = str(uuid.uuid4())
    logger.info({"event": "content_generation_start", "draft_id": draft_id, "business_id": business_id, "format": format})

    # Carrega brand context unificado
    brand_ctx = get_unified_brand_context(business_id)
    ig_style = brand_ctx.get("business", {}).get("brand_context", {}).get("instagram_style")

    # 1. Gera script via Claude
    script = await generate_post_script(
        business_type=business_type,
        business_name=business_name,
        objective=objective,
        tone=tone,
        audience=audience,
        format=format,
        brand_strategy=brand_strategy,
        slide_count=slide_count,
        instagram_style=ig_style,
    )
    logger.info({"event": "script_generated", "draft_id": draft_id})

    # 2. Imagem/Vídeo: usa uploaded ou gera via IA
    image_url = None
    image_urls = None
    video_url = None

    if uploaded_image_url:
        image_url = uploaded_image_url
        logger.info({"event": "using_uploaded_image", "draft_id": draft_id, "url": image_url})

    try:
        if uploaded_image_url:
            pass  # Já atribuído acima
        elif format == "carrossel":
            slides = script.get("slides", [])
            slide_descriptions = [s.get("visual_description", objective) for s in slides]
            # Gera cada slide sequencialmente para evitar rate limit
            urls = []
            for desc in slide_descriptions:
                try:
                    img_bytes = await generate_image(
                        visual_description=desc,
                        format="post",
                        brand_context=brand_ctx,
                    )
                    url = await upload_image(img_bytes, "post")
                    urls.append(url)
                except Exception as slide_err:
                    logger.warning({"event": "carousel_slide_failed", "error": str(slide_err)})
            image_urls = urls if urls else None
            image_url = urls[0] if urls else None
            logger.info({"event": "carousel_images_generated", "draft_id": draft_id, "count": len(urls)})
        else:
            # Gera imagem (para post, story, reel)
            image_bytes_gen = await generate_image(
                visual_description=script.get("visual_description", objective),
                format=format,
                brand_context=brand_ctx,
            )
            image_url = await upload_image(image_bytes_gen, format)
            logger.info({"event": "image_generated", "draft_id": draft_id, "url": image_url})

            # Para reel: tenta gerar vídeo a partir da imagem
            if format == "reel" and image_bytes_gen:
                try:
                    from src.engines.video_engine.composer import compose_reel
                    reel_result = await compose_reel(
                        image_bytes=image_bytes_gen,
                        video_prompt=script.get("visual_description", objective)[:500],
                        narration_text=script.get("caption", "")[:300],
                        duration=5,
                    )
                    if reel_result.get("video_url"):
                        video_url = reel_result["video_url"]
                        logger.info({"event": "reel_video_generated", "draft_id": draft_id, "url": video_url})
                except Exception as ve:
                    logger.warning({"event": "reel_video_skipped", "draft_id": draft_id, "error": str(ve)})
    except Exception as e:
        logger.error({"event": "image_generation_failed", "draft_id": draft_id, "error": str(e)})

    # 3. Salva ContentDraft no banco
    import json
    now = datetime.utcnow()

    # Para carrossel, visual_description é o JSON dos slides
    visual_desc = script.get("visual_description")
    if format == "carrossel" and script.get("slides"):
        visual_desc = json.dumps(script["slides"], ensure_ascii=False)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO content_drafts
                  (id, business_id, format, caption, hashtags, image_url, image_urls,
                   video_url, visual_description, call_to_action, best_posting_time,
                   status, criado_em, atualizado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending_approval', %s, %s)
                """,
                (
                    draft_id,
                    business_id,
                    format,
                    script.get("caption", ""),
                    json.dumps(script.get("hashtags", []), ensure_ascii=False),
                    image_url,
                    json.dumps(image_urls, ensure_ascii=False) if image_urls else None,
                    video_url,
                    visual_desc,
                    script.get("call_to_action"),
                    script.get("best_posting_time"),
                    now,
                    now,
                ),
            )

    logger.info({"event": "content_draft_saved", "draft_id": draft_id})

    return {
        "id": draft_id,
        "business_id": business_id,
        "format": format,
        "caption": script.get("caption", ""),
        "hashtags": script.get("hashtags", []),
        "image_url": image_url,
        "image_urls": image_urls,
        "video_url": video_url,
        "visual_description": visual_desc,
        "call_to_action": script.get("call_to_action"),
        "best_posting_time": script.get("best_posting_time"),
        "status": "pending_approval",
        "criado_em": now.isoformat(),
    }

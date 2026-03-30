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
) -> dict[str, Any]:
    """
    Orquestra geração completa: script → imagem → salva draft.
    Retorna o ContentDraft criado.
    """
    draft_id = str(uuid.uuid4())
    logger.info({"event": "content_generation_start", "draft_id": draft_id, "business_id": business_id})

    # 1. Gera script via Claude
    script = await generate_post_script(
        business_type=business_type,
        business_name=business_name,
        objective=objective,
        tone=tone,
        audience=audience,
        format=format,
        brand_strategy=brand_strategy,
    )
    logger.info({"event": "script_generated", "draft_id": draft_id})

    # 2. Gera imagem com brand context para qualidade máxima
    brand_ctx = get_unified_brand_context(business_id)
    image_url = None
    try:
        image_bytes = await generate_image(
            visual_description=script.get("visual_description", objective),
            format=format,
            brand_context=brand_ctx,
        )
        image_url = await upload_image(image_bytes, format)
        logger.info({"event": "image_generated", "draft_id": draft_id, "url": image_url})
    except Exception as e:
        logger.error({"event": "image_generation_failed", "draft_id": draft_id, "error": str(e)})
        # Continua sem imagem — usuário poderá adicionar manualmente

    # 3. Salva ContentDraft no banco
    import json
    now = datetime.utcnow()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO content_drafts
                  (id, business_id, format, caption, hashtags, image_url,
                   visual_description, call_to_action, best_posting_time,
                   status, criado_em, atualizado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending_approval', %s, %s)
                """,
                (
                    draft_id,
                    business_id,
                    format,
                    script.get("caption", ""),
                    json.dumps(script.get("hashtags", []), ensure_ascii=False),
                    image_url,
                    script.get("visual_description"),
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
        "visual_description": script.get("visual_description"),
        "call_to_action": script.get("call_to_action"),
        "best_posting_time": script.get("best_posting_time"),
        "status": "pending_approval",
        "criado_em": now.isoformat(),
    }

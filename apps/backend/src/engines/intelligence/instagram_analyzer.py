"""
Instagram Style Analyzer — Analisa posts existentes via Graph API para
entender o estilo visual, tom de escrita e padrões de conteúdo do perfil.
"""
import json
import logging
from typing import Any

import anthropic

from src.db.connection import get_connection
from src.engines.publisher.instagram import fetch_recent_posts
from src.engines.publisher.token_manager import decrypt_token

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic()

ANALYSIS_PROMPT = """Analise estes {post_count} posts recentes do Instagram do negócio "{business_name}" ({business_type}).

POSTS:
{posts_text}

Analise o estilo do perfil e retorne APENAS JSON válido:
{{
  "writing_style": {{
    "tone": "tom predominante (ex: profissional e acolhedor, descontraído e direto, educativo, etc.)",
    "caption_length": "curta (<100 chars) | média (100-500) | longa (500+)",
    "uses_emojis": true/false,
    "emoji_style": "quais emojis usa mais (ex: ✨🔥💡) ou 'nenhum'",
    "uses_hashtags": true/false,
    "hashtag_count_avg": 0,
    "uses_cta": true/false,
    "cta_examples": ["exemplos de CTAs usados"],
    "language_patterns": "padrões de escrita (ex: usa perguntas, inicia com emoji, usa listas, etc.)"
  }},
  "visual_style": {{
    "dominant_aesthetic": "descrição da estética visual (ex: clean e minimalista, vibrante e colorido, escuro e sofisticado, etc.)",
    "color_palette": "paleta predominante (ex: tons quentes, azul e branco, cores neutras, etc.)",
    "photo_style": "estilo das fotos (ex: produto em estúdio, lifestyle, flat lay, antes/depois, etc.)",
    "composition": "composição típica (ex: centralizado, regra dos terços, close-up, etc.)",
    "consistency_level": "alta | média | baixa — quão consistente é o feed visualmente"
  }},
  "content_patterns": {{
    "main_themes": ["tema1", "tema2", "tema3"],
    "content_mix": "mix de tipos (ex: 60% educativo, 20% promo, 20% bastidores)",
    "posting_frequency": "estimativa baseada nos timestamps",
    "best_performing_topics": ["temas que parecem gerar mais engajamento baseado nos captions"]
  }},
  "image_prompt_guide": "EM INGLÊS: Um parágrafo de 100-150 palavras descrevendo EXATAMENTE como gerar imagens que combinem com este feed. Inclua: estilo fotográfico, paleta de cores, mood, iluminação, composição, nível de saturação, e qualquer elemento recorrente. Este texto será usado como guia para IA geradora de imagem."
}}"""


async def analyze_instagram_style(business_id: str) -> dict[str, Any]:
    """
    Busca posts recentes do Instagram conectado e analisa o estilo completo.
    Salva resultado no brand_context do business.
    """
    # Buscar dados do business
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, type, instagram_account_id, instagram_access_token FROM businesses WHERE id = %s",
                (business_id,),
            )
            biz = cur.fetchone()

    if not biz:
        return {"success": False, "error": "Business não encontrado"}
    if not biz.get("instagram_account_id") or not biz.get("instagram_access_token"):
        return {"success": False, "error": "Instagram não conectado neste business"}

    # Buscar posts recentes
    try:
        access_token = decrypt_token(biz["instagram_access_token"])
        posts = await fetch_recent_posts(
            instagram_account_id=biz["instagram_account_id"],
            access_token=access_token,
            limit=12,
        )
    except Exception as e:
        logger.error({"event": "ig_fetch_posts_failed", "business_id": business_id, "error": str(e)})
        return {"success": False, "error": f"Erro ao buscar posts: {str(e)}"}

    if not posts:
        return {"success": False, "error": "Nenhum post encontrado no Instagram"}

    # Montar texto dos posts para análise
    posts_text = []
    for i, p in enumerate(posts, 1):
        caption = (p.get("caption") or "").strip()
        media_type = p.get("media_type", "IMAGE")
        timestamp = p.get("timestamp", "")[:10]
        posts_text.append(
            f"Post {i} ({media_type}, {timestamp}):\n{caption if caption else '[sem legenda]'}"
        )

    prompt = ANALYSIS_PROMPT.format(
        post_count=len(posts),
        business_name=biz["name"],
        business_type=biz["type"],
        posts_text="\n\n".join(posts_text),
    )

    # Analisar com Claude
    try:
        response = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system="Você é um especialista em marketing digital que analisa perfis de Instagram. Retorne APENAS JSON válido, sem markdown.",
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3].strip()
        analysis = json.loads(raw)
    except Exception as e:
        logger.error({"event": "ig_analysis_failed", "business_id": business_id, "error": str(e)})
        return {"success": False, "error": f"Erro na análise: {str(e)}"}

    # Salvar no brand_context do business
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT brand_context FROM businesses WHERE id = %s", (business_id,))
            row = cur.fetchone()
            existing_ctx = {}
            if row and row.get("brand_context"):
                ctx = row["brand_context"]
                if isinstance(ctx, str):
                    try:
                        existing_ctx = json.loads(ctx)
                    except Exception:
                        existing_ctx = {}
                elif isinstance(ctx, dict):
                    existing_ctx = ctx

            existing_ctx["instagram_style"] = analysis
            cur.execute(
                "UPDATE businesses SET brand_context = %s, atualizado_em = NOW() WHERE id = %s",
                (json.dumps(existing_ctx, ensure_ascii=False), business_id),
            )

    logger.info({"event": "ig_style_analyzed", "business_id": business_id, "posts": len(posts)})
    return {
        "success": True,
        "posts_analyzed": len(posts),
        "analysis": analysis,
    }

import os
import json
import logging
from typing import Any
import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

SYSTEM_PROMPT = """
Você é um especialista em marketing digital e copywriting para redes sociais.
Sempre gere conteúdo em português brasileiro.
Retorne APENAS JSON válido, sem markdown, sem explicações extras.
"""

POST_PROMPT = """
Crie um post para Instagram para o seguinte negócio:

Tipo de negócio: {business_type}
Nome da empresa: {business_name}
Objetivo do post: {objective}
Tom de voz: {tone}
Público-alvo: {audience}

Retorne exatamente neste formato JSON:
{{
  "caption": "texto do post (máx 2200 chars)",
  "hashtags": ["lista", "de", "hashtags", "relevantes"],
  "visual_description": "descrição detalhada da imagem ideal para este post",
  "call_to_action": "texto do CTA",
  "best_posting_time": "horário sugerido HH:MM"
}}
"""

STORY_PROMPT = """
Crie um story para Instagram:

Tipo de negócio: {business_type}
Nome da empresa: {business_name}
Objetivo: {objective}

Retorne JSON:
{{
  "caption": "texto curto para legenda (máx 200 chars)",
  "hashtags": ["hashtags", "relevantes"],
  "visual_description": "descrição detalhada do visual do story 9:16",
  "call_to_action": "texto do CTA",
  "text_overlay": "texto principal (máx 30 palavras)",
  "best_posting_time": "HH:MM"
}}
"""


async def generate_post_script(
    business_type: str,
    business_name: str,
    objective: str,
    tone: str = "profissional",
    audience: str = "geral",
    format: str = "post",
    brand_strategy: dict | None = None,
) -> dict[str, Any]:
    prompt_template = STORY_PROMPT if format == "story" else POST_PROMPT
    user_prompt = prompt_template.format(
        business_type=business_type,
        business_name=business_name,
        objective=objective,
        tone=tone,
        audience=audience,
    )

    if brand_strategy:
        extra_parts = []
        if brand_strategy.get("content_pillars"):
            extra_parts.append(f"Pilares de conteúdo da marca: {', '.join(str(p) for p in brand_strategy['content_pillars'])}")
        if brand_strategy.get("brand_tone"):
            extra_parts.append(f"Tom de voz definido pela marca: {brand_strategy['brand_tone']}")
        if brand_strategy.get("goals"):
            extra_parts.append(f"Objetivos da marca: {', '.join(str(g) for g in brand_strategy['goals'])}")
        if extra_parts:
            user_prompt += "\n\nContexto adicional da estratégia de marca:\n" + "\n".join(extra_parts)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = message.content[0].text.strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error({"event": "script_engine_json_error", "error": str(e)})
        raise ValueError(f"Claude retornou JSON inválido: {e}")
    except Exception as e:
        logger.error({"event": "script_engine_error", "error": str(e)})
        raise

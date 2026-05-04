import os
import json
import logging
from typing import Any
import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

SYSTEM_PROMPT = """Você é um diretor criativo de uma agência de marketing digital premium.
Você cria conteúdo em português brasileiro E escreve prompts de geração de imagem em INGLÊS (pois modelos de IA geram imagens melhores com prompts em inglês).
Retorne APENAS JSON válido, sem markdown, sem explicações extras."""

POST_PROMPT = """Crie um post para Instagram para o seguinte negócio:

Tipo de negócio: {business_type}
Nome da empresa: {business_name}
Objetivo do post: {objective}
Tom de voz: {tone}
Público-alvo: {audience}

Retorne exatamente neste formato JSON:
{{
  "caption": "texto do post em português brasileiro (máx 2200 chars, com quebras de linha para legibilidade)",
  "hashtags": ["lista", "de", "hashtags", "relevantes"],
  "visual_description": "PROMPT DE IMAGEM EM INGLÊS — veja instruções abaixo",
  "call_to_action": "texto do CTA em português",
  "best_posting_time": "HH:MM"
}}

INSTRUÇÕES PARA visual_description (CRÍTICO — qualidade da imagem depende disso):
Escreva EM INGLÊS um prompt de 80-150 palavras no estilo de prompts profissionais de IA (Midjourney/DALL-E).
O prompt DEVE incluir TODOS estes elementos:
1. SUBJECT: O que aparece na imagem (pessoa, produto, cena, objetos)
2. SETTING: Ambiente (estúdio, ao ar livre, escritório, loja, etc.)
3. LIGHTING: Tipo de iluminação (natural soft light, golden hour, studio lighting with softbox, etc.)
4. COMPOSITION: Enquadramento (close-up, wide angle, overhead flat lay, centered, rule of thirds)
5. MOOD: Atmosfera (warm and inviting, clean and professional, vibrant and energetic, luxurious)
6. STYLE: Estilo fotográfico (commercial product photography, lifestyle editorial, minimalist, etc.)
7. TECHNICAL: Qualidade (8K, shallow depth of field, sharp focus, professional color grading)
8. NEGATIVE: O que NÃO deve aparecer (no text, no watermarks, no logos, no graphic overlays)
Formato quadrado 1:1 para feed do Instagram. Fotorrealista, qualidade de revista.
"""

STORY_PROMPT = """Crie um story para Instagram:

Tipo de negócio: {business_type}
Nome da empresa: {business_name}
Objetivo: {objective}
Tom de voz: {tone}
Público-alvo: {audience}

Retorne JSON:
{{
  "caption": "texto curto para legenda em português (máx 200 chars)",
  "hashtags": ["hashtags", "relevantes"],
  "visual_description": "PROMPT DE IMAGEM EM INGLÊS — veja instruções abaixo",
  "call_to_action": "texto do CTA",
  "text_overlay": "texto principal em português (máx 30 palavras)",
  "best_posting_time": "HH:MM"
}}

INSTRUÇÕES PARA visual_description (CRÍTICO):
Escreva EM INGLÊS um prompt de 80-150 palavras para uma imagem vertical 9:16 (story).
Inclua: SUBJECT, SETTING, LIGHTING, COMPOSITION (vertical full-bleed, portrait orientation),
MOOD, STYLE, TECHNICAL (8K, sharp, professional), NEGATIVE (no text, no watermarks).
A imagem deve funcionar como fundo de story com texto sobreposto.
"""

CAROUSEL_PROMPT = """Crie um carrossel com {slide_count} slides para Instagram:

Tipo de negócio: {business_type}
Nome da empresa: {business_name}
Objetivo: {objective}
Tom de voz: {tone}
Público-alvo: {audience}

Retorne JSON:
{{
  "caption": "caption em português brasileiro (gancho forte na 1ª linha, máx 2200 chars)",
  "hashtags": ["mix", "de", "hashtags"],
  "call_to_action": "CTA em português",
  "best_posting_time": "HH:MM",
  "slides": [
    {{
      "visual_description": "PROMPT DE IMAGEM EM INGLÊS (80-150 palavras)",
      "text_overlay": "frase de impacto em português (máx 15 palavras)"
    }}
  ]
}}

REGRAS DO CARROSSEL:
- Gere exatamente {slide_count} slides
- SLIDE 1: visual impactante + frase que gera curiosidade
- SLIDES DO MEIO: narrativa progressiva, cada slide = 1 insight
- ÚLTIMO SLIDE: CTA visual forte

INSTRUÇÕES PARA visual_description DE CADA SLIDE:
Escreva EM INGLÊS 80-150 palavras. Formato quadrado 1:1.
Inclua: SUBJECT, SETTING, LIGHTING, COMPOSITION, MOOD, STYLE, TECHNICAL (8K, professional).
NEGATIVE: no text, no watermarks, no logos.
Todos os slides devem ter a MESMA paleta de cores e estilo visual — como uma sessão fotográfica.
"""


async def generate_post_script(
    business_type: str,
    business_name: str,
    objective: str,
    tone: str = "profissional",
    audience: str = "geral",
    format: str = "post",
    brand_strategy: dict | None = None,
    **kwargs,
) -> dict[str, Any]:
    if format == "carrossel":
        slide_count = kwargs.get("slide_count", 5)
        user_prompt = CAROUSEL_PROMPT.format(
            business_type=business_type,
            business_name=business_name,
            objective=objective,
            tone=tone,
            audience=audience,
            slide_count=slide_count,
        )
    elif format == "story":
        user_prompt = STORY_PROMPT.format(
            business_type=business_type,
            business_name=business_name,
            objective=objective,
            tone=tone,
            audience=audience,
        )
    else:
        user_prompt = POST_PROMPT.format(
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
        # Visual identity — inject into image prompt guidance
        if brand_strategy.get("visual_identity"):
            vi = brand_strategy["visual_identity"]
            color_parts = []
            if vi.get("primary_color"):
                color_parts.append(vi["primary_color"])
            if vi.get("secondary_color"):
                color_parts.append(vi["secondary_color"])
            if vi.get("accent_color"):
                color_parts.append(vi["accent_color"])

            vi_instruction = "OBRIGATÓRIO na visual_description (prompt de imagem em inglês):\n"
            if color_parts:
                vi_instruction += f"- Inclua na paleta de cores: color palette featuring {', '.join(color_parts)}\n"
            if vi.get("style_description"):
                vi_instruction += f"- Estilo visual da marca: {vi['style_description']}\n"
            vi_instruction += "- As cores e o estilo da marca DEVEM estar presentes na atmosfera/cenário da imagem."
            extra_parts.append(vi_instruction)
        if extra_parts:
            user_prompt += "\n\nContexto adicional da estratégia de marca:\n" + "\n".join(extra_parts)

    # Instagram style — análise dos posts existentes do perfil
    ig_style = kwargs.get("instagram_style") or {}
    if ig_style:
        ig_parts = ["\n\nESTILO DO INSTAGRAM EXISTENTE (siga para manter consistência):"]
        ws = ig_style.get("writing_style", {})
        if ws.get("tone"):
            ig_parts.append(f"- Tom de escrita: {ws['tone']}")
        if ws.get("caption_length"):
            ig_parts.append(f"- Tamanho de caption: {ws['caption_length']}")
        vs = ig_style.get("visual_style", {})
        if vs.get("dominant_aesthetic"):
            ig_parts.append(f"- Estética visual: {vs['dominant_aesthetic']}")
        if ig_style.get("image_prompt_guide"):
            ig_parts.append(f"- GUIA para visual_description: {ig_style['image_prompt_guide']}")
        user_prompt += "\n".join(ig_parts)

    try:
        max_tok = 4096 if format == "carrossel" else 2048
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tok,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3].strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error({"event": "script_engine_json_error", "error": str(e)})
        raise ValueError(f"Claude retornou JSON inválido: {e}")
    except Exception as e:
        logger.error({"event": "script_engine_error", "error": str(e)})
        raise

"""
Unified Brand Context — Monta perfil completo da marca para injetar nos agentes.
Combina dados de: businesses + brand_strategy + visual_identity
"""
import json
import logging
from typing import Any

from src.db.connection import get_connection

logger = logging.getLogger(__name__)


def get_unified_brand_context(business_id: str) -> dict[str, Any]:
    """
    Consulta as 3 tabelas e retorna o contexto completo da marca.
    Retorna dict vazio se business não existir.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Business
            cur.execute(
                "SELECT id, name, type, brand_context FROM businesses WHERE id = %s",
                (business_id,),
            )
            biz = cur.fetchone()
            if not biz:
                return {}

            # Brand strategy
            cur.execute(
                "SELECT * FROM brand_strategy WHERE business_id = %s",
                (business_id,),
            )
            strategy = cur.fetchone()

            # Visual identity
            cur.execute(
                "SELECT * FROM visual_identity WHERE business_id = %s",
                (business_id,),
            )
            identity = cur.fetchone()

    # Parse JSON fields from business
    brand_ctx = biz.get("brand_context")
    if brand_ctx and isinstance(brand_ctx, str):
        try:
            brand_ctx = json.loads(brand_ctx)
        except Exception:
            brand_ctx = {}

    # Parse JSON fields from strategy
    strategy_data = {}
    if strategy:
        json_fields = ["personas", "content_pillars", "posting_frequency", "brand_colors", "competitors", "goals"]
        for f in json_fields:
            val = strategy.get(f)
            if val and isinstance(val, str):
                try:
                    strategy_data[f] = json.loads(val)
                except Exception:
                    strategy_data[f] = val
            elif val:
                strategy_data[f] = val
        if strategy.get("brand_tone"):
            strategy_data["brand_tone"] = strategy["brand_tone"]

    # Parse JSON fields from identity
    identity_data = {}
    if identity:
        for key in [
            "primary_color", "secondary_color", "accent_color",
            "background_color", "text_color", "font_heading", "font_body",
            "style_description", "logo_url", "extra_context",
        ]:
            if identity.get(key):
                identity_data[key] = identity[key]

        ref_urls = identity.get("reference_image_urls")
        if ref_urls and isinstance(ref_urls, str):
            try:
                identity_data["reference_image_urls"] = json.loads(ref_urls)
            except Exception:
                pass
        elif ref_urls:
            identity_data["reference_image_urls"] = ref_urls

    return {
        "business": {
            "id": biz["id"],
            "name": biz.get("name", ""),
            "type": biz.get("type", ""),
            "brand_context": brand_ctx or {},
        },
        "strategy": strategy_data,
        "visual_identity": identity_data,
    }


def brand_context_to_prompt(context: dict[str, Any]) -> str:
    """
    Converte o contexto unificado em bloco de texto para injetar no system prompt.
    """
    if not context or not context.get("business"):
        return ""

    biz = context["business"]
    strategy = context.get("strategy", {})
    vi = context.get("visual_identity", {})

    parts = [
        f"\n═══ CONTEXTO COMPLETO DA MARCA ═══",
        f"Empresa: {biz.get('name', '?')} ({biz.get('type', '?')})",
        f"Business ID: {biz.get('id', '?')}",
    ]

    # Strategy
    if strategy:
        parts.append("\n── Estratégia de Marca ──")
        if strategy.get("brand_tone"):
            parts.append(f"Tom de voz: {strategy['brand_tone']}")
        if strategy.get("content_pillars"):
            pillars = strategy["content_pillars"]
            if isinstance(pillars, list):
                parts.append(f"Pilares de conteúdo: {', '.join(str(p) for p in pillars)}")
        if strategy.get("goals"):
            goals = strategy["goals"]
            if isinstance(goals, list):
                parts.append(f"Objetivos: {', '.join(str(g) for g in goals)}")
        if strategy.get("personas"):
            parts.append(f"Personas: {json.dumps(strategy['personas'], ensure_ascii=False)}")
        if strategy.get("competitors"):
            comps = strategy["competitors"]
            if isinstance(comps, list):
                parts.append(f"Concorrentes: {', '.join(str(c) for c in comps)}")
        if strategy.get("posting_frequency"):
            freq = strategy["posting_frequency"]
            if isinstance(freq, dict) and freq.get("posts_per_week"):
                parts.append(f"Frequência: {freq['posts_per_week']} posts/semana")
        if strategy.get("brand_colors"):
            colors = strategy["brand_colors"]
            if isinstance(colors, list):
                parts.append(f"Cores da estratégia: {', '.join(str(c) for c in colors)}")

    # Visual Identity
    if vi:
        parts.append("\n── Identidade Visual ──")
        color_fields = [
            ("primary_color", "Cor primária"),
            ("secondary_color", "Cor secundária"),
            ("accent_color", "Cor de acento"),
            ("background_color", "Cor de fundo"),
            ("text_color", "Cor do texto"),
        ]
        for field, label in color_fields:
            if vi.get(field):
                parts.append(f"{label}: {vi[field]}")

        if vi.get("font_heading"):
            parts.append(f"Fonte títulos: {vi['font_heading']}")
        if vi.get("font_body"):
            parts.append(f"Fonte corpo: {vi['font_body']}")
        if vi.get("style_description"):
            parts.append(f"Estilo visual: {vi['style_description']}")
        if vi.get("logo_url"):
            parts.append(f"Logo: {vi['logo_url']}")
        if vi.get("extra_context"):
            parts.append(f"Contexto extra: {vi['extra_context']}")

    # Instagram Style Analysis (se existir)
    ig_style = biz.get("brand_context", {}).get("instagram_style")
    if ig_style:
        parts.append("\n── Estilo do Instagram (análise dos posts existentes) ──")
        ws = ig_style.get("writing_style", {})
        if ws:
            parts.append(f"Tom de escrita: {ws.get('tone', '?')}")
            parts.append(f"Tamanho das captions: {ws.get('caption_length', '?')}")
            if ws.get("uses_emojis"):
                parts.append(f"Emojis usados: {ws.get('emoji_style', 'sim')}")
            if ws.get("language_patterns"):
                parts.append(f"Padrões de escrita: {ws['language_patterns']}")
            if ws.get("cta_examples"):
                parts.append(f"CTAs típicos: {', '.join(ws['cta_examples'][:3])}")
        vs = ig_style.get("visual_style", {})
        if vs:
            parts.append(f"Estética visual: {vs.get('dominant_aesthetic', '?')}")
            parts.append(f"Paleta predominante: {vs.get('color_palette', '?')}")
            parts.append(f"Estilo fotográfico: {vs.get('photo_style', '?')}")
        cp = ig_style.get("content_patterns", {})
        if cp and cp.get("main_themes"):
            parts.append(f"Temas principais: {', '.join(cp['main_themes'])}")
        if ig_style.get("image_prompt_guide"):
            parts.append(f"Guia de imagem: {ig_style['image_prompt_guide']}")

    parts.append("═══════════════════════════════\n")
    return "\n".join(parts)

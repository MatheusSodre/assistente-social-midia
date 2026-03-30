"""
Sofia — Diretora Criativa / Brand Manager IA
Orquestra Mara (Social Media), Pixel (Designer) e Luna (Google Ads).
"""
import json
import logging
import uuid
from typing import Any

import anthropic

from src.db.connection import get_connection
from src.engines.brand_context import get_unified_brand_context, brand_context_to_prompt

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic()

# Haiku para tudo — economia de ~75% vs Sonnet, qualidade suficiente para coordenação
MODEL_SMART = "claude-haiku-4-5-20251001"
MODEL_FAST = "claude-haiku-4-5-20251001"

SOFIA_SYSTEM = """Você é Sofia, Diretora Criativa de uma agência de marketing digital.
Fala português brasileiro de forma direta, profissional e calorosa.

REGRA #1 — AÇÃO PRIMEIRO:
Quando o cliente pedir para criar conteúdo, CRIE IMEDIATAMENTE usando create_content_direct. Não fique fazendo perguntas antes. Use o que já sabe sobre o negócio (nome, tipo, descrição) e crie. O cliente pode ajustar depois.

QUANDO PERGUNTAR (e só nestes casos):
- Se o cliente disser "olá" ou algo genérico sem pedir nada específico → apresente-se em 2 frases e pergunte o que ele precisa
- Se o cliente pedir algo mas você não tem o mínimo (nem sabe o tipo do negócio) → pergunte APENAS o essencial
- Se o cliente mandar um link → analise com analyze_client_url e salve os dados

COMO CRIAR CONTEÚDO:
1. Cliente pede "cria um post sobre X" → use create_content_direct imediatamente
2. Cliente pede "cria uma semana de conteúdo" → use create_content_direct várias vezes com temas variados
3. Após criar, mostre um resumo curto: tema, formato, e diga que está em "Revisar & Aprovar"

SUA EQUIPE (use quando necessário):
- delegate_to_mara → análise de performance, calendário editorial, aprovações em lote
- delegate_to_pixel → edição de imagens, identidade visual
- delegate_to_luna → Google Ads, campanhas pagas

COMUNICAÇÃO:
- Respostas curtas e diretas, máximo 3-4 parágrafos
- Não repita informações que o cliente já sabe
- Após ações, ofereça 1-2 próximos passos
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_brand_profile",
        "description": "Retorna o perfil completo da marca: negócio, estratégia e identidade visual.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "update_brand_strategy",
        "description": "Atualiza a estratégia de marca (tom, pilares, goals, personas, etc).",
        "input_schema": {
            "type": "object",
            "properties": {
                "content_pillars": {"type": "array", "items": {"type": "string"}},
                "brand_tone": {"type": "string"},
                "posting_frequency": {"type": "object"},
                "goals": {"type": "array", "items": {"type": "string"}},
                "personas": {"type": "array", "items": {"type": "object"}},
                "competitors": {"type": "array", "items": {"type": "string"}},
                "brand_colors": {"type": "array", "items": {"type": "string"}},
            },
            "required": [],
        },
    },
    {
        "name": "update_visual_identity",
        "description": "Atualiza a identidade visual da marca (cores, fontes, estilo).",
        "input_schema": {
            "type": "object",
            "properties": {
                "primary_color": {"type": "string", "description": "Cor primária hex (#RRGGBB)"},
                "secondary_color": {"type": "string"},
                "accent_color": {"type": "string"},
                "background_color": {"type": "string"},
                "text_color": {"type": "string"},
                "font_heading": {"type": "string"},
                "font_body": {"type": "string"},
                "style_description": {"type": "string"},
                "extra_context": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "create_content_direct",
        "description": "Cria um post/story/reel DIRETO (mais rápido e barato). Use esta tool para criação simples de conteúdo ao invés de delegate_to_mara.",
        "input_schema": {
            "type": "object",
            "properties": {
                "objective": {"type": "string", "description": "Objetivo ou tema do conteúdo"},
                "format": {"type": "string", "enum": ["post", "story", "reel"], "description": "Formato"},
                "tone": {"type": "string", "enum": ["profissional", "descontraido", "urgente", "educativo"], "description": "Tom de voz"},
                "audience": {"type": "string", "description": "Público-alvo"},
            },
            "required": ["objective"],
        },
    },
    {
        "name": "delegate_to_mara",
        "description": "Delega tarefa COMPLEXA para Mara (análise de performance, calendário editorial, aprovações em lote). Para CRIAR conteúdo simples, prefira create_content_direct.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Descrição da tarefa para Mara executar"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_pixel",
        "description": "Delega uma tarefa para Pixel (Designer Visual). Use para editar imagens, aplicar identidade visual, criar visuais brandados.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Descrição da tarefa para Pixel executar"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_luna",
        "description": "Delega uma tarefa para Luna (Google Ads). Use para analisar campanhas, sugerir keywords, otimizar budget.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Descrição da tarefa para Luna executar"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "get_content_overview",
        "description": "Visão geral do conteúdo: drafts pendentes, aprovados, publicados, performance.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_pending_drafts",
        "description": "Lista rascunhos de conteúdo aguardando aprovação.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "check_readiness",
        "description": "Verifica o quanto o perfil do negócio está completo (score 0-100%). Use SEMPRE no início da conversa para saber se pode criar conteúdo ou precisa coletar mais informações.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "analyze_client_url",
        "description": "Analisa o site, Instagram ou LinkedIn do cliente para extrair informações sobre o negócio automaticamente. Use quando o cliente enviar um link.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL do site, Instagram ou LinkedIn do cliente"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "update_business_profile",
        "description": "Atualiza o perfil do negócio com informações coletadas na conversa (descrição, serviços, público-alvo, diferenciais, localização).",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Descrição do negócio"},
                "services": {"type": "array", "items": {"type": "string"}, "description": "Lista de produtos/serviços"},
                "target_audience": {"type": "string", "description": "Público-alvo"},
                "differentials": {"type": "string", "description": "Diferenciais do negócio"},
                "location": {"type": "string", "description": "Cidade/região"},
                "website_url": {"type": "string", "description": "URL do site"},
                "instagram_handle": {"type": "string", "description": "@ do Instagram"},
            },
            "required": [],
        },
    },
]


# ─── Tool Executors ──────────────────────────────────────────────────────────

def _exec_get_brand_profile(business_id: str) -> dict:
    ctx = get_unified_brand_context(business_id)
    if not ctx:
        return {"error": "Business não encontrado"}
    return ctx


def _exec_update_brand_strategy(business_id: str, tool_input: dict) -> dict:
    json_fields = ["content_pillars", "posting_frequency", "goals", "personas", "brand_colors", "competitors"]
    fields = {k: v for k, v in tool_input.items() if v is not None}
    if not fields:
        return {"success": False, "message": "Nenhum campo fornecido"}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM brand_strategy WHERE business_id = %s", (business_id,))
            existing = cur.fetchone()
            if existing:
                set_parts = []
                params = []
                for k, v in fields.items():
                    set_parts.append(f"{k} = %s")
                    params.append(json.dumps(v, ensure_ascii=False) if k in json_fields else v)
                params.append(business_id)
                cur.execute(
                    f"UPDATE brand_strategy SET {', '.join(set_parts)}, atualizado_em = NOW() WHERE business_id = %s",
                    params,
                )
            else:
                sid = str(uuid.uuid4())
                col_names = ["id", "business_id"] + list(fields.keys())
                placeholders = ["%s"] * len(col_names)
                values = [sid, business_id] + [
                    json.dumps(v, ensure_ascii=False) if k in json_fields else v
                    for k, v in fields.items()
                ]
                cur.execute(
                    f"INSERT INTO brand_strategy ({', '.join(col_names)}) VALUES ({', '.join(placeholders)})",
                    values,
                )
    return {"success": True, "message": "Estratégia atualizada!", "fields": list(fields.keys())}


def _exec_update_visual_identity(business_id: str, tool_input: dict) -> dict:
    allowed = {
        "primary_color", "secondary_color", "accent_color", "background_color",
        "text_color", "font_heading", "font_body", "style_description",
        "logo_url", "extra_context",
    }
    clean = {k: v for k, v in tool_input.items() if k in allowed and v is not None}
    if not clean:
        return {"success": False, "message": "Nenhum campo válido"}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM visual_identity WHERE business_id = %s", (business_id,))
            existing = cur.fetchone()
            if existing:
                set_parts = [f"{k} = %s" for k in clean]
                params = list(clean.values()) + [business_id]
                cur.execute(
                    f"UPDATE visual_identity SET {', '.join(set_parts)}, atualizado_em = NOW() WHERE business_id = %s",
                    params,
                )
            else:
                row_id = str(uuid.uuid4())
                cols = ["id", "business_id"] + list(clean.keys())
                placeholders = ["%s"] * len(cols)
                vals = [row_id, business_id] + list(clean.values())
                cur.execute(
                    f"INSERT INTO visual_identity ({', '.join(cols)}) VALUES ({', '.join(placeholders)})",
                    vals,
                )
    return {"success": True, "message": "Identidade visual atualizada!", "fields": list(clean.keys())}


async def _exec_create_content_direct(business_id: str, tool_input: dict) -> dict:
    """Cria conteúdo direto via orchestrator — bypassa Mara, economiza ~3 chamadas Claude."""
    from src.engines.orchestrator import generate_content
    brand_ctx = get_unified_brand_context(business_id)
    biz = brand_ctx.get("business", {})
    strategy = brand_ctx.get("strategy", {})
    vi = brand_ctx.get("visual_identity", {})
    enriched = dict(strategy) if strategy else {}
    if vi:
        enriched["visual_identity"] = vi

    try:
        draft = await generate_content(
            business_id=business_id,
            business_name=biz.get("name", "empresa"),
            business_type=biz.get("type", "negócio"),
            objective=tool_input["objective"],
            format=tool_input.get("format", "post"),
            tone=tool_input.get("tone", "profissional"),
            audience=tool_input.get("audience", "geral"),
            brand_strategy=enriched if enriched else None,
        )
        return {
            "success": True,
            "draft_id": draft["id"],
            "caption": draft.get("caption", "")[:300],
            "hashtags": draft.get("hashtags", []),
            "image_url": draft.get("image_url"),
            "format": draft.get("format"),
            "status": "pending_approval",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _exec_delegate_to_mara(business_id: str, usuario_id: str, task: str) -> dict:
    from src.engines.agent.social_media_agent import run_agent
    try:
        result = await run_agent(
            business_id=business_id,
            usuario_id=usuario_id,
            user_message=task,
            ephemeral=True,
        )
        return {"agent": "mara", "success": True, "response": result["response"]}
    except Exception as e:
        logger.error({"event": "sofia_delegate_mara_error", "error": str(e)})
        return {"agent": "mara", "success": False, "error": str(e)}


async def _exec_delegate_to_pixel(business_id: str, usuario_id: str, task: str) -> dict:
    from src.engines.designer.pixel_agent import run_pixel
    try:
        result = await run_pixel(
            business_id=business_id,
            usuario_id=usuario_id,
            user_message=task,
            ephemeral=True,
        )
        return {
            "agent": "pixel",
            "success": True,
            "response": result["response"],
            "image_url": result.get("image_url"),
        }
    except Exception as e:
        logger.error({"event": "sofia_delegate_pixel_error", "error": str(e)})
        return {"agent": "pixel", "success": False, "error": str(e)}


async def _exec_delegate_to_luna(business_id: str, usuario_id: str, task: str) -> dict:
    from src.engines.ads_agent.luna_agent import run_luna
    try:
        result = await run_luna(
            business_id=business_id,
            usuario_id=usuario_id,
            user_message=task,
            ephemeral=True,
        )
        return {"agent": "luna", "success": True, "response": result["response"]}
    except Exception as e:
        logger.error({"event": "sofia_delegate_luna_error", "error": str(e)})
        return {"agent": "luna", "success": False, "error": str(e)}


def _exec_check_readiness(business_id: str) -> dict:
    """Computa readiness score do perfil do negócio."""
    from api.business.router import _compute_readiness
    return _compute_readiness(business_id)


async def _exec_analyze_client_url(business_id: str, url: str) -> dict:
    """Scrape e analisa URL do cliente, auto-merge no perfil."""
    from src.engines.intelligence.web_scraper import analyze_website
    from api.business.router import _auto_merge, _compute_readiness
    result = await analyze_website(url)
    if result.get("error"):
        return {"success": False, "error": result["error"]}
    _auto_merge(business_id, result)
    readiness_data = _compute_readiness(business_id)
    return {"success": True, "extracted": result, "readiness": readiness_data}


def _exec_update_business_profile(business_id: str, tool_input: dict) -> dict:
    """Atualiza campos do perfil do negócio."""
    allowed = {"description", "services", "target_audience", "differentials", "location", "website_url", "instagram_handle"}
    fields = {k: v for k, v in tool_input.items() if k in allowed and v is not None}
    if not fields:
        return {"success": False, "message": "Nenhum campo fornecido"}

    updates = {}
    for k, v in fields.items():
        if k == "services" and isinstance(v, list):
            updates[k] = json.dumps(v, ensure_ascii=False)
        else:
            updates[k] = v

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [business_id]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE businesses SET {set_clause}, atualizado_em = NOW() WHERE id = %s",
                values,
            )

    from api.business.router import _compute_readiness
    readiness_data = _compute_readiness(business_id)
    return {"success": True, "updated_fields": list(fields.keys()), "readiness": readiness_data}


def _exec_content_overview(business_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT
                     COUNT(*) as total,
                     SUM(CASE WHEN status = 'pending_approval' THEN 1 ELSE 0 END) as pending,
                     SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                     SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                     SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published
                   FROM content_drafts WHERE business_id = %s""",
                (business_id,),
            )
            totals = cur.fetchone() or {}

            cur.execute(
                """SELECT format, COUNT(*) as cnt FROM content_drafts
                   WHERE business_id = %s AND status IN ('approved','published')
                   GROUP BY format ORDER BY cnt DESC""",
                (business_id,),
            )
            by_format = cur.fetchall() or []

    total = totals.get("total") or 0
    approved = (totals.get("approved") or 0) + (totals.get("published") or 0)
    rate = round((approved / total * 100) if total > 0 else 0, 1)

    return {
        "total_drafts": total,
        "pending_approval": totals.get("pending") or 0,
        "approved": totals.get("approved") or 0,
        "published": totals.get("published") or 0,
        "rejected": totals.get("rejected") or 0,
        "approval_rate_pct": rate,
        "top_formats": [{"format": r["format"], "count": r["cnt"]} for r in by_format],
    }


def _exec_list_pending(business_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, format, caption, image_url, criado_em
                   FROM content_drafts
                   WHERE business_id = %s AND status = 'pending_approval'
                   ORDER BY criado_em DESC LIMIT 10""",
                (business_id,),
            )
            rows = cur.fetchall() or []
    return {
        "pending_count": len(rows),
        "drafts": [
            {
                "id": r["id"],
                "format": r["format"],
                "caption": (r["caption"] or "")[:150],
                "image_url": r.get("image_url"),
            }
            for r in rows
        ],
    }


# ─── Conversation Persistence ────────────────────────────────────────────────

def _load_conversation(business_id: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT messages FROM agency_conversations WHERE business_id = %s",
                (business_id,),
            )
            row = cur.fetchone()
    if not row:
        return []
    msgs = row["messages"]
    if isinstance(msgs, str):
        msgs = json.loads(msgs)
    return msgs or []


def _compact_messages(messages: list[dict]) -> list[dict]:
    """Compacta tool_result para economizar tokens no histórico."""
    compacted = []
    for msg in messages:
        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
            # Compactar tool_results — manter só resumo
            compact_content = []
            for item in msg["content"]:
                if item.get("type") == "tool_result":
                    try:
                        data = json.loads(item["content"]) if isinstance(item["content"], str) else item["content"]
                        # Resumir para max 200 chars
                        summary = json.dumps(data, ensure_ascii=False, default=str)[:200]
                        compact_content.append({**item, "content": summary})
                    except Exception:
                        compact_content.append(item)
                else:
                    compact_content.append(item)
            compacted.append({"role": msg["role"], "content": compact_content})
        else:
            compacted.append(msg)
    return compacted


def _save_conversation(business_id: str, usuario_id: str, messages: list[dict]) -> None:
    compacted = _compact_messages(messages)
    trimmed = compacted[-20:] if len(compacted) > 20 else compacted
    msgs_json = json.dumps(trimmed, ensure_ascii=False, default=str)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM agency_conversations WHERE business_id = %s", (business_id,))
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE agency_conversations SET messages = %s, atualizado_em = NOW() WHERE business_id = %s",
                    (msgs_json, business_id),
                )
            else:
                cur.execute(
                    "INSERT INTO agency_conversations (id, business_id, usuario_id, messages) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), business_id, usuario_id, msgs_json),
                )


def _block_to_dict(block) -> dict:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return {"type": block.type}


# ─── Main Agent Function ─────────────────────────────────────────────────────

async def run_sofia(
    business_id: str,
    usuario_id: str,
    user_message: str,
) -> dict[str, Any]:
    """
    Loop agêntico da Sofia — Diretora Criativa.
    Pode delegar para Mara, Pixel e Luna.
    """
    brand_ctx = get_unified_brand_context(business_id)
    history = _load_conversation(business_id)
    history.append({"role": "user", "content": user_message})

    system = SOFIA_SYSTEM + brand_context_to_prompt(brand_ctx)

    messages = list(history)
    max_iterations = 10
    steps: list[dict] = []
    iteration = 0

    for iteration in range(max_iterations):
        # Sonnet para primeira chamada (raciocínio), Haiku para followups de tools (mais barato)
        model = MODEL_SMART if iteration == 0 else MODEL_FAST
        response = _client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        content_dicts = [_block_to_dict(b) for b in response.content]
        messages.append({"role": "assistant", "content": content_dicts})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_name = block.name
            tool_input = block.input
            logger.info({"event": "sofia_tool_call", "tool": tool_name, "business_id": business_id})

            try:
                if tool_name == "create_content_direct":
                    result = await _exec_create_content_direct(business_id, tool_input)
                    steps.append({"agent": "mara", "action": f"Criou {tool_input.get('format','post')}: {tool_input['objective'][:60]}", "status": "done" if result.get("success") else "error"})
                elif tool_name == "get_brand_profile":
                    result = _exec_get_brand_profile(business_id)
                elif tool_name == "update_brand_strategy":
                    result = _exec_update_brand_strategy(business_id, tool_input)
                    brand_ctx = get_unified_brand_context(business_id)
                    system = SOFIA_SYSTEM + brand_context_to_prompt(brand_ctx)
                elif tool_name == "update_visual_identity":
                    result = _exec_update_visual_identity(business_id, tool_input)
                    brand_ctx = get_unified_brand_context(business_id)
                    system = SOFIA_SYSTEM + brand_context_to_prompt(brand_ctx)
                elif tool_name == "delegate_to_mara":
                    result = await _exec_delegate_to_mara(business_id, usuario_id, tool_input["task"])
                    steps.append({"agent": "mara", "action": tool_input["task"][:100], "status": "done" if result.get("success") else "error"})
                elif tool_name == "delegate_to_pixel":
                    result = await _exec_delegate_to_pixel(business_id, usuario_id, tool_input["task"])
                    steps.append({"agent": "pixel", "action": tool_input["task"][:100], "status": "done" if result.get("success") else "error"})
                elif tool_name == "delegate_to_luna":
                    result = await _exec_delegate_to_luna(business_id, usuario_id, tool_input["task"])
                    steps.append({"agent": "luna", "action": tool_input["task"][:100], "status": "done" if result.get("success") else "error"})
                elif tool_name == "get_content_overview":
                    result = _exec_content_overview(business_id)
                elif tool_name == "list_pending_drafts":
                    result = _exec_list_pending(business_id)
                elif tool_name == "check_readiness":
                    result = _exec_check_readiness(business_id)
                elif tool_name == "analyze_client_url":
                    result = await _exec_analyze_client_url(business_id, tool_input["url"])
                    steps.append({"agent": "sofia", "action": f"Analisou {tool_input['url'][:50]}", "status": "done" if result.get("success") else "error"})
                elif tool_name == "update_business_profile":
                    result = _exec_update_business_profile(business_id, tool_input)
                    brand_ctx = get_unified_brand_context(business_id)
                    system = SOFIA_SYSTEM + brand_context_to_prompt(brand_ctx)
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
            except Exception as e:
                logger.error({"event": "sofia_tool_error", "tool": tool_name, "error": str(e)})
                result = {"error": str(e)}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

        messages.append({"role": "user", "content": tool_results})

    final_text = ""
    for block in response.content:
        if block.type == "text":
            final_text = block.text
            break

    _save_conversation(business_id, usuario_id, messages)

    return {
        "response": final_text or "Tarefa executada!",
        "steps": steps,
        "message_count": len(messages),
    }

"""
Mara — Agente Social Media IA
Loop agentico com tool_use do Claude.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

import anthropic

from src.db.connection import get_connection
from src.engines.orchestrator import generate_content

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic()

MARA_SYSTEM = """Você é Mara, especialista sênior em Social Media com 10 anos de experiência.
Você é estratégica, criativa e orientada a resultados. Fala português brasileiro de forma clara e amigável.
Você tem acesso a ferramentas para criar conteúdo, analisar performance e gerenciar o calendário editorial do cliente.

Quando o usuário pedir conteúdo, use as ferramentas disponíveis para executar de verdade — não apenas sugira.
Após executar ações, apresente os resultados de forma resumida e ofereça próximos passos.
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "generate_content",
        "description": "Gera um post/story/reel completo (texto + imagem) para o business. Use quando o usuário pedir para criar conteúdo individual.",
        "input_schema": {
            "type": "object",
            "properties": {
                "objective": {"type": "string", "description": "Objetivo ou tema do conteúdo"},
                "format": {"type": "string", "enum": ["post", "story", "reel"], "description": "Formato"},
                "tone": {"type": "string", "enum": ["profissional", "descontraido", "urgente", "educativo"], "description": "Tom de voz"},
                "audience": {"type": "string", "description": "Público-alvo (ex: 'mulheres 25-35 anos')"},
            },
            "required": ["objective", "format"],
        },
    },
    {
        "name": "generate_batch_content",
        "description": "Gera múltiplos posts em paralelo. Use quando o usuário pedir uma semana ou lote de conteúdo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "Lista de conteúdos a gerar (máx 7)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "objective": {"type": "string"},
                            "format": {"type": "string", "enum": ["post", "story", "reel"]},
                            "tone": {"type": "string", "enum": ["profissional", "descontraido", "urgente", "educativo"]},
                            "audience": {"type": "string"},
                        },
                        "required": ["objective", "format"],
                    },
                    "maxItems": 7,
                },
            },
            "required": ["items"],
        },
    },
    {
        "name": "list_pending_drafts",
        "description": "Lista os rascunhos aguardando aprovação do usuário.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "approve_draft",
        "description": "Aprova um rascunho de conteúdo pelo ID.",
        "input_schema": {
            "type": "object",
            "properties": {"draft_id": {"type": "string", "description": "ID do rascunho"}},
            "required": ["draft_id"],
        },
    },
    {
        "name": "schedule_draft",
        "description": "Aprova e agenda um rascunho para publicação em uma data/hora específica.",
        "input_schema": {
            "type": "object",
            "properties": {
                "draft_id": {"type": "string"},
                "scheduled_for": {"type": "string", "description": "Data e hora no formato ISO 8601 (ex: 2026-03-15T14:00:00)"},
            },
            "required": ["draft_id", "scheduled_for"],
        },
    },
    {
        "name": "get_post_history",
        "description": "Retorna histórico de posts publicados.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "Número de posts (padrão 10)", "default": 10}},
            "required": [],
        },
    },
    {
        "name": "analyze_performance",
        "description": "Analisa a performance do conteúdo: taxa de aprovação, formatos mais usados, horários populares.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "suggest_editorial_calendar",
        "description": "Sugere um calendário editorial com temas para os próximos dias baseado na estratégia de marca.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Número de dias (padrão 7, máx 30)", "default": 7},
            },
            "required": [],
        },
    },
    {
        "name": "get_business_info",
        "description": "Retorna informações do business e estratégia de marca atual.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "update_brand_strategy",
        "description": "Atualiza a estratégia de marca do business.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content_pillars": {"type": "array", "items": {"type": "string"}, "description": "Pilares de conteúdo"},
                "brand_tone": {"type": "string", "description": "Tom de voz da marca"},
                "posting_frequency": {"type": "object", "description": "Frequência de posts (ex: {'posts_per_week': 5})"},
                "goals": {"type": "array", "items": {"type": "string"}, "description": "Objetivos da estratégia"},
            },
            "required": [],
        },
    },
]


# ─── Tool Executors ───────────────────────────────────────────────────────────

async def _exec_generate_content(business_id: str, business_name: str, business_type: str,
                                  brand_strategy: dict | None, tool_input: dict) -> dict:
    draft = await generate_content(
        business_id=business_id,
        business_name=business_name,
        business_type=business_type,
        objective=tool_input["objective"],
        format=tool_input.get("format", "post"),
        tone=tool_input.get("tone", "profissional"),
        audience=tool_input.get("audience", "geral"),
        brand_strategy=brand_strategy,
    )
    return {
        "success": True,
        "draft_id": draft["id"],
        "caption": draft["caption"][:200] + "..." if len(draft.get("caption", "")) > 200 else draft.get("caption", ""),
        "image_url": draft.get("image_url"),
        "status": "pending_approval",
        "message": f"Conteúdo criado! ID: {draft['id']}. Aguarda aprovação.",
    }


async def _exec_generate_batch(business_id: str, business_name: str, business_type: str,
                                brand_strategy: dict | None, tool_input: dict) -> dict:
    items = tool_input.get("items", [])[:7]
    tasks = [
        generate_content(
            business_id=business_id,
            business_name=business_name,
            business_type=business_type,
            objective=item["objective"],
            format=item.get("format", "post"),
            tone=item.get("tone", "profissional"),
            audience=item.get("audience", "geral"),
            brand_strategy=brand_strategy,
        )
        for item in items
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    drafts = []
    errors = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            errors.append(f"Item {i+1}: {str(r)}")
        else:
            drafts.append({"draft_id": r["id"], "objective": items[i]["objective"], "format": items[i].get("format", "post")})
    return {"success": True, "created": len(drafts), "drafts": drafts, "errors": errors}


def _exec_list_pending(business_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, format, caption, criado_em
                   FROM content_drafts
                   WHERE business_id = %s AND status = 'pending_approval'
                   ORDER BY criado_em DESC LIMIT 10""",
                (business_id,),
            )
            rows = cur.fetchall() or []
    return {"pending_count": len(rows), "drafts": [
        {"id": r["id"], "format": r["format"], "caption": (r["caption"] or "")[:100]}
        for r in rows
    ]}


def _exec_approve_draft(business_id: str, draft_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE content_drafts SET status = 'approved', atualizado_em = NOW()
                   WHERE id = %s AND business_id = %s AND status = 'pending_approval'""",
                (draft_id, business_id),
            )
            updated = cur.rowcount
    if updated == 0:
        return {"success": False, "message": "Draft não encontrado ou já processado"}
    return {"success": True, "draft_id": draft_id, "message": "Conteúdo aprovado!"}


def _exec_schedule_draft(business_id: str, draft_id: str, scheduled_for: str) -> dict:
    try:
        scheduled_dt = datetime.fromisoformat(scheduled_for)
    except ValueError:
        return {"success": False, "message": f"Data inválida: {scheduled_for}"}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE content_drafts SET status = 'approved', scheduled_for = %s, atualizado_em = NOW()
                   WHERE id = %s AND business_id = %s""",
                (scheduled_dt, draft_id, business_id),
            )
            if cur.rowcount == 0:
                return {"success": False, "message": "Draft não encontrado"}
            sp_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO scheduled_posts (id, content_draft_id, platform, scheduled_for, status)
                   VALUES (%s, %s, 'instagram', %s, 'scheduled')""",
                (sp_id, draft_id, scheduled_dt),
            )
    return {"success": True, "draft_id": draft_id, "scheduled_for": scheduled_for, "message": "Agendado!"}


def _exec_post_history(business_id: str, limit: int = 10) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT sp.id, sp.platform, sp.posted_at, sp.status,
                          cd.format, cd.caption, cd.image_url
                   FROM scheduled_posts sp
                   JOIN content_drafts cd ON cd.id = sp.content_draft_id
                   WHERE cd.business_id = %s
                   ORDER BY sp.criado_em DESC LIMIT %s""",
                (business_id, min(limit, 20)),
            )
            rows = cur.fetchall() or []
    return {"total": len(rows), "posts": [
        {"id": r["id"], "format": r.get("format"), "posted_at": str(r.get("posted_at", "")),
         "status": r["status"], "caption": (r.get("caption") or "")[:100]}
        for r in rows
    ]}


def _exec_analyze_performance(business_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT
                     COUNT(*) as total_drafts,
                     SUM(CASE WHEN status = 'approved' OR status = 'published' THEN 1 ELSE 0 END) as approved,
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

            cur.execute(
                """SELECT best_posting_time, COUNT(*) as cnt FROM content_drafts
                   WHERE business_id = %s AND best_posting_time IS NOT NULL
                   GROUP BY best_posting_time ORDER BY cnt DESC LIMIT 5""",
                (business_id,),
            )
            best_times = cur.fetchall() or []

    total = totals.get("total_drafts") or 0
    approved = totals.get("approved") or 0
    approval_rate = round((approved / total * 100) if total > 0 else 0, 1)

    return {
        "total_drafts": total,
        "approved": approved,
        "rejected": totals.get("rejected") or 0,
        "published": totals.get("published") or 0,
        "approval_rate_pct": approval_rate,
        "top_formats": [{"format": r["format"], "count": r["cnt"]} for r in by_format],
        "best_times": [{"time": r["best_posting_time"], "count": r["cnt"]} for r in best_times],
    }


def _exec_suggest_calendar(business_id: str, brand_strategy: dict | None, days: int = 7) -> dict:
    pillars = []
    frequency = {}
    if brand_strategy:
        pillars = brand_strategy.get("content_pillars") or []
        frequency = brand_strategy.get("posting_frequency") or {}

    if not pillars:
        pillars = ["educativo", "promocional", "inspiracional", "bastidores", "depoimento"]

    posts_per_week = frequency.get("posts_per_week", 5) if frequency else 5
    days = min(days, 30)

    suggestions = []
    today = datetime.utcnow().date()
    posts_count = 0
    max_posts = round(posts_per_week * days / 7)

    formats_cycle = ["post", "story", "post", "reel", "post", "story", "post"]

    day_offset = 0
    pillar_idx = 0
    while posts_count < max_posts and day_offset < days:
        date = today + timedelta(days=day_offset)
        # Skip Sunday for most businesses
        if date.weekday() < 6:
            suggestions.append({
                "date": str(date),
                "theme": pillars[pillar_idx % len(pillars)],
                "format": formats_cycle[posts_count % len(formats_cycle)],
                "day_of_week": date.strftime("%A"),
            })
            posts_count += 1
            pillar_idx += 1
        day_offset += 1

    return {"days": days, "suggestions": suggestions, "total_suggested": len(suggestions)}


def _exec_get_business_info(business_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, type, instagram_account_id, brand_context FROM businesses WHERE id = %s",
                (business_id,),
            )
            biz = cur.fetchone()
            cur.execute(
                "SELECT * FROM brand_strategy WHERE business_id = %s",
                (business_id,),
            )
            strategy = cur.fetchone()

    if not biz:
        return {"error": "Business não encontrado"}

    json_fields = ["brand_context"]
    for f in json_fields:
        if biz.get(f) and isinstance(biz[f], str):
            biz[f] = json.loads(biz[f])

    if strategy:
        for f in ["personas", "content_pillars", "posting_frequency", "brand_colors", "competitors", "goals"]:
            if strategy.get(f) and isinstance(strategy[f], str):
                strategy[f] = json.loads(strategy[f])

    return {
        "business": {k: v for k, v in biz.items() if k != "instagram_access_token"},
        "brand_strategy": strategy,
    }


def _exec_update_brand_strategy(business_id: str, tool_input: dict) -> dict:
    import json as _json
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
                    params.append(_json.dumps(v, ensure_ascii=False) if k in json_fields else v)
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
                    _json.dumps(v, ensure_ascii=False) if k in json_fields else v
                    for k, v in fields.items()
                ]
                cur.execute(
                    f"INSERT INTO brand_strategy ({', '.join(col_names)}) VALUES ({', '.join(placeholders)})",
                    values,
                )

    return {"success": True, "message": "Estratégia atualizada!", "updated_fields": list(fields.keys())}


# ─── Conversation Persistence ─────────────────────────────────────────────────

def _load_conversation(business_id: str, usuario_id: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT messages FROM agent_conversations WHERE business_id = %s",
                (business_id,),
            )
            row = cur.fetchone()
    if not row:
        return []
    msgs = row["messages"]
    if isinstance(msgs, str):
        msgs = json.loads(msgs)
    return msgs or []


def _save_conversation(business_id: str, usuario_id: str, messages: list[dict]) -> None:
    # Keep last 40 messages
    trimmed = messages[-40:] if len(messages) > 40 else messages
    msgs_json = json.dumps(trimmed, ensure_ascii=False, default=str)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM agent_conversations WHERE business_id = %s",
                (business_id,),
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE agent_conversations SET messages = %s, atualizado_em = NOW() WHERE business_id = %s",
                    (msgs_json, business_id),
                )
            else:
                cur.execute(
                    "INSERT INTO agent_conversations (id, business_id, usuario_id, messages) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), business_id, usuario_id, msgs_json),
                )


def _block_to_dict(block) -> dict:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return {"type": block.type}


# ─── Main Agent Function ──────────────────────────────────────────────────────

async def run_agent(
    business_id: str,
    usuario_id: str,
    user_message: str,
) -> dict[str, Any]:
    """
    Executa o loop agentico da Mara e retorna a resposta final.
    """
    # Load business info for context
    biz_info = _exec_get_business_info(business_id)
    business = biz_info.get("business", {})
    brand_strategy = biz_info.get("brand_strategy")
    business_name = business.get("name", "empresa")
    business_type = business.get("type", "negócio")

    # Load conversation history
    history = _load_conversation(business_id, usuario_id)

    # Add new user message
    history.append({"role": "user", "content": user_message})

    system_with_context = (
        f"{MARA_SYSTEM}\n\n"
        f"Business atual: {business_name} (tipo: {business_type})\n"
        f"Business ID: {business_id}\n"
    )
    if brand_strategy and brand_strategy.get("content_pillars"):
        pillars = brand_strategy.get("content_pillars", [])
        system_with_context += f"Pilares de conteúdo: {', '.join(str(p) for p in pillars)}\n"
    if brand_strategy and brand_strategy.get("brand_tone"):
        system_with_context += f"Tom de voz: {brand_strategy['brand_tone']}\n"

    messages = list(history)
    max_iterations = 10

    for _ in range(max_iterations):
        response = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_with_context,
            tools=TOOLS,
            messages=messages,
        )

        # Append assistant response to messages
        content_dicts = [_block_to_dict(b) for b in response.content]
        messages.append({"role": "assistant", "content": content_dicts})

        if response.stop_reason != "tool_use":
            break

        # Execute all tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_name = block.name
            tool_input = block.input
            logger.info({"event": "agent_tool_call", "tool": tool_name, "business_id": business_id})

            try:
                if tool_name == "generate_content":
                    result = await _exec_generate_content(
                        business_id, business_name, business_type, brand_strategy, tool_input
                    )
                elif tool_name == "generate_batch_content":
                    result = await _exec_generate_batch(
                        business_id, business_name, business_type, brand_strategy, tool_input
                    )
                elif tool_name == "list_pending_drafts":
                    result = _exec_list_pending(business_id)
                elif tool_name == "approve_draft":
                    result = _exec_approve_draft(business_id, tool_input["draft_id"])
                elif tool_name == "schedule_draft":
                    result = _exec_schedule_draft(business_id, tool_input["draft_id"], tool_input["scheduled_for"])
                elif tool_name == "get_post_history":
                    result = _exec_post_history(business_id, tool_input.get("limit", 10))
                elif tool_name == "analyze_performance":
                    result = _exec_analyze_performance(business_id)
                elif tool_name == "suggest_editorial_calendar":
                    result = _exec_suggest_calendar(business_id, brand_strategy, tool_input.get("days", 7))
                elif tool_name == "get_business_info":
                    result = _exec_get_business_info(business_id)
                elif tool_name == "update_brand_strategy":
                    result = _exec_update_brand_strategy(business_id, tool_input)
                    # Refresh brand_strategy after update
                    biz_info = _exec_get_business_info(business_id)
                    brand_strategy = biz_info.get("brand_strategy")
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
            except Exception as e:
                logger.error({"event": "agent_tool_error", "tool": tool_name, "error": str(e)})
                result = {"error": str(e)}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

        messages.append({"role": "user", "content": tool_results})

    # Extract final text response
    final_text = ""
    for block in response.content:
        if block.type == "text":
            final_text = block.text
            break

    if not final_text:
        final_text = "Ação executada com sucesso!"

    # Save updated conversation (strip tool_result messages for cleaner history,
    # but keep tool_use blocks so context is preserved)
    _save_conversation(business_id, usuario_id, messages)

    return {
        "response": final_text,
        "message_count": len(messages),
    }

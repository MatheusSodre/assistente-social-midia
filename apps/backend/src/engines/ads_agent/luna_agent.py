"""
Luna — Agente Google Ads IA
Loop agentico com tool_use do Claude especializado em Google Ads.
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

MODEL_SMART = "claude-haiku-4-5-20251001"
MODEL_FAST = "claude-haiku-4-5-20251001"

LUNA_SYSTEM = """Você é Luna, especialista em Google Ads e tráfego pago.

QUEM VOCÊ É:
Com 8 anos gerenciando campanhas de performance, você já otimizou mais de R$ 5 milhões em budget publicitário. Você é a pessoa que transforma dinheiro investido em resultados mensuráveis. Começou como analista em agências e hoje é a referência em mídia paga da equipe.

SUA PERSONALIDADE:
- Analítica mas acessível: adora números mas sabe que o cliente quer entender o impacto, não a planilha
- Transparente: se um investimento não está funcionando, você fala. Se está, celebra com dados
- Estratégica: não pensa só em cliques, pensa em conversões e ROI real
- Didática: explica conceitos como CTR, CPC e ROAS de forma que qualquer pessoa entenda
- Protetora do budget: trata o dinheiro do cliente como se fosse seu

COMO TRABALHAR:
- Sempre apresente métricas em formato legível: R$ 1.240,00 (não 1240000000 micros)
- Quando analisar performance, dê 2-3 insights acionáveis, não só números
- Sugira otimizações: "Essa campanha tem CTR baixo, podemos testar novos títulos?"
- Se a conta não está conectada, explique claramente que os dados são demonstrativos
- Relacione os anúncios com a estratégia de conteúdo da marca quando possível

IMPORTANTE: Dados marcados como [MOCK] são demonstrativos — a conta real de Google Ads não está conectada. Informe isso de forma natural, sem ser repetitiva.

Fale português brasileiro de forma profissional e acessível. Seja a consultora que o cliente confia para investir bem.
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_ads_account",
        "description": "Verifica se o business tem uma conta Google Ads conectada e retorna informações da conta.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_account_overview",
        "description": "Retorna métricas gerais da conta Google Ads nos últimos 30 dias: impressões, cliques, custo, CTR, conversões.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_campaigns",
        "description": "Lista todas as campanhas com suas métricas de performance (impressões, cliques, custo, CTR).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "pause_campaign",
        "description": "Pausa uma campanha ativa.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string", "description": "ID da campanha"},
                "campaign_name": {"type": "string", "description": "Nome da campanha (para confirmação)"},
            },
            "required": ["campaign_id"],
        },
    },
    {
        "name": "enable_campaign",
        "description": "Ativa uma campanha pausada.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string", "description": "ID da campanha"},
                "campaign_name": {"type": "string", "description": "Nome da campanha (para confirmação)"},
            },
            "required": ["campaign_id"],
        },
    },
    {
        "name": "get_keywords",
        "description": "Lista as palavras-chave de uma campanha com métricas de performance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string", "description": "ID da campanha (opcional, retorna todas se omitido)"},
            },
            "required": [],
        },
    },
    {
        "name": "suggest_keywords",
        "description": "Sugere palavras-chave relevantes para o negócio com base no tipo de negócio e objetivos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "theme": {"type": "string", "description": "Tema ou produto/serviço para gerar keywords"},
                "match_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["BROAD", "PHRASE", "EXACT"]},
                    "description": "Tipos de correspondência desejados",
                },
            },
            "required": ["theme"],
        },
    },
    {
        "name": "update_budget",
        "description": "Atualiza o orçamento diário de uma campanha.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "new_daily_budget_brl": {"type": "number", "description": "Novo orçamento diário em R$"},
            },
            "required": ["campaign_id", "new_daily_budget_brl"],
        },
    },
    {
        "name": "analyze_performance",
        "description": "Analisa a performance geral e dá recomendações estratégicas com base nos dados.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_business_info",
        "description": "Retorna informações do business para contexto estratégico.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ─── DB helpers ───────────────────────────────────────────────────────────────

def _get_ads_account(business_id: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM google_ads_accounts WHERE business_id = %s",
                (business_id,),
            )
            return cur.fetchone()


def _get_business(business_id: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, type, brand_context FROM businesses WHERE id = %s",
                (business_id,),
            )
            row = cur.fetchone()
    if row and row.get("brand_context") and isinstance(row["brand_context"], str):
        import json as _json
        row["brand_context"] = _json.loads(row["brand_context"])
    return row


def _load_conversation(business_id: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT messages FROM luna_conversations WHERE business_id = %s",
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
    trimmed = messages[-20:] if len(messages) > 20 else messages
    msgs_json = json.dumps(trimmed, ensure_ascii=False, default=str)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM luna_conversations WHERE business_id = %s",
                (business_id,),
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE luna_conversations SET messages = %s, atualizado_em = NOW() WHERE business_id = %s",
                    (msgs_json, business_id),
                )
            else:
                cur.execute(
                    "INSERT INTO luna_conversations (id, business_id, usuario_id, messages) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), business_id, usuario_id, msgs_json),
                )


def _block_to_dict(block) -> dict:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return {"type": block.type}


# ─── Tool Executors ───────────────────────────────────────────────────────────

def _exec_get_ads_account(business_id: str) -> dict:
    account = _get_ads_account(business_id)
    if not account:
        return {
            "connected": False,
            "message": "Conta Google Ads não conectada. Vá em Google Ads > Conectar Conta para adicionar as credenciais.",
        }
    return {
        "connected": True,
        "customer_id": account["customer_id"],
        "is_test_account": bool(account["is_test_account"]),
        "has_credentials": bool(account.get("refresh_token")),
    }


def _try_real_or_mock(business_id: str, real_fn, mock_data, fn_name: str):
    """Try to call the real Google Ads API, fall back to mock data."""
    account = _get_ads_account(business_id)
    if not account or not account.get("refresh_token"):
        logger.info({"event": "ads_mock_data", "fn": fn_name, "business_id": business_id})
        result = mock_data if not callable(mock_data) else mock_data()
        if isinstance(result, list):
            return {"data": result, "note": "[MOCK] Conta não conectada — dados demonstrativos"}
        return {**result, "note": "[MOCK] Conta não conectada — dados demonstrativos"}
    try:
        from src.engines.ads.google_ads_client import build_client
        client = build_client(
            refresh_token=account["refresh_token"],
            customer_id=account["customer_id"],
            login_customer_id=account.get("login_customer_id"),
        )
        return real_fn(client, account["customer_id"])
    except Exception as e:
        logger.error({"event": "ads_api_error", "fn": fn_name, "error": str(e)})
        return {"error": str(e), "note": "Erro na API Google Ads"}


def _exec_account_overview(business_id: str) -> dict:
    from src.engines.ads.google_ads_client import get_account_overview, MOCK_OVERVIEW
    return _try_real_or_mock(
        business_id,
        lambda client, cid: get_account_overview(client, cid),
        MOCK_OVERVIEW,
        "get_account_overview",
    )


def _exec_list_campaigns(business_id: str) -> dict:
    from src.engines.ads.google_ads_client import get_campaigns, MOCK_CAMPAIGNS
    return _try_real_or_mock(
        business_id,
        lambda client, cid: {"campaigns": get_campaigns(client, cid)},
        {"campaigns": MOCK_CAMPAIGNS},
        "list_campaigns",
    )


def _exec_pause_campaign(business_id: str, campaign_id: str) -> dict:
    account = _get_ads_account(business_id)
    if not account or not account.get("refresh_token"):
        return {"success": False, "note": "[MOCK] Campanha pausada (simulado)", "campaign_id": campaign_id}
    try:
        from src.engines.ads.google_ads_client import build_client, pause_campaign
        client = build_client(account["refresh_token"], account["customer_id"], account.get("login_customer_id"))
        return pause_campaign(client, account["customer_id"], campaign_id)
    except Exception as e:
        return {"error": str(e)}


def _exec_enable_campaign(business_id: str, campaign_id: str) -> dict:
    account = _get_ads_account(business_id)
    if not account or not account.get("refresh_token"):
        return {"success": False, "note": "[MOCK] Campanha ativada (simulado)", "campaign_id": campaign_id}
    try:
        from src.engines.ads.google_ads_client import build_client, enable_campaign
        client = build_client(account["refresh_token"], account["customer_id"], account.get("login_customer_id"))
        return enable_campaign(client, account["customer_id"], campaign_id)
    except Exception as e:
        return {"error": str(e)}


def _exec_get_keywords(business_id: str, campaign_id: str | None = None) -> dict:
    from src.engines.ads.google_ads_client import get_keywords, MOCK_KEYWORDS
    return _try_real_or_mock(
        business_id,
        lambda client, cid: {"keywords": get_keywords(client, cid, campaign_id)},
        {"keywords": MOCK_KEYWORDS},
        "get_keywords",
    )


def _exec_suggest_keywords(business_id: str, business_name: str, business_type: str,
                            theme: str, match_types: list[str]) -> dict:
    """Use Claude to suggest keywords."""
    match_types = match_types or ["BROAD", "PHRASE", "EXACT"]
    prompt = f"""Sugira 15 palavras-chave Google Ads para:
Negócio: {business_name} ({business_type})
Tema/Produto: {theme}

Para cada keyword, inclua os tipos: {', '.join(match_types)}
Retorne JSON com esta estrutura:
{{
  "keywords": [
    {{"text": "palavra-chave", "match_type": "BROAD|PHRASE|EXACT", "reason": "por que usar"}}
  ]
}}
Retorne APENAS JSON válido."""

    response = _client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    import json as _json
    try:
        return _json.loads(response.content[0].text.strip())
    except Exception:
        return {"keywords": [], "raw": response.content[0].text}


def _exec_update_budget(business_id: str, campaign_id: str, new_daily_budget_brl: float) -> dict:
    account = _get_ads_account(business_id)
    if not account or not account.get("refresh_token"):
        return {
            "success": False,
            "note": f"[MOCK] Orçamento atualizado para R$ {new_daily_budget_brl:.2f}/dia (simulado)",
            "campaign_id": campaign_id,
        }
    try:
        from src.engines.ads.google_ads_client import build_client, update_campaign_budget
        client = build_client(account["refresh_token"], account["customer_id"], account.get("login_customer_id"))
        return update_campaign_budget(client, account["customer_id"], campaign_id, new_daily_budget_brl)
    except Exception as e:
        return {"error": str(e)}


def _exec_analyze_performance(business_id: str) -> dict:
    """Get overview + campaigns for analysis context."""
    overview = _exec_account_overview(business_id)
    campaigns_data = _exec_list_campaigns(business_id)
    campaigns = campaigns_data.get("campaigns", [])

    # Basic analysis
    enabled = [c for c in campaigns if c["status"] == "ENABLED"]
    paused = [c for c in campaigns if c["status"] == "PAUSED"]
    top_by_cost = sorted(enabled, key=lambda c: c["cost_brl"], reverse=True)[:3]
    low_ctr = [c for c in enabled if c["ctr_pct"] < 1.0]

    return {
        "overview": overview,
        "total_campaigns": len(campaigns),
        "active_campaigns": len(enabled),
        "paused_campaigns": len(paused),
        "top_spend_campaigns": top_by_cost,
        "low_ctr_campaigns": low_ctr,
        "is_mock": "note" in overview,
    }


def _exec_get_business_info(business_id: str) -> dict:
    biz = _get_business(business_id)
    if not biz:
        return {"error": "Business não encontrado"}
    return {"name": biz.get("name"), "type": biz.get("type")}


# ─── Main Agent Function ──────────────────────────────────────────────────────

async def run_luna(business_id: str, usuario_id: str, user_message: str, ephemeral: bool = False) -> dict[str, Any]:
    brand_ctx = get_unified_brand_context(business_id)
    business = brand_ctx.get("business", {})
    business_name = business.get("name", "empresa")
    business_type = business.get("type", "negócio")

    history = [] if ephemeral else _load_conversation(business_id)
    history.append({"role": "user", "content": user_message})

    system = LUNA_SYSTEM + brand_context_to_prompt(brand_ctx)

    messages = list(history)
    max_iterations = 8

    for iteration in range(max_iterations):
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
            logger.info({"event": "luna_tool_call", "tool": tool_name, "business_id": business_id})

            try:
                if tool_name == "get_ads_account":
                    result = _exec_get_ads_account(business_id)
                elif tool_name == "get_account_overview":
                    result = _exec_account_overview(business_id)
                elif tool_name == "list_campaigns":
                    result = _exec_list_campaigns(business_id)
                elif tool_name == "pause_campaign":
                    result = _exec_pause_campaign(business_id, tool_input["campaign_id"])
                elif tool_name == "enable_campaign":
                    result = _exec_enable_campaign(business_id, tool_input["campaign_id"])
                elif tool_name == "get_keywords":
                    result = _exec_get_keywords(business_id, tool_input.get("campaign_id"))
                elif tool_name == "suggest_keywords":
                    result = _exec_suggest_keywords(
                        business_id, business_name, business_type,
                        tool_input["theme"],
                        tool_input.get("match_types", ["BROAD", "PHRASE", "EXACT"]),
                    )
                elif tool_name == "update_budget":
                    result = _exec_update_budget(
                        business_id, tool_input["campaign_id"], tool_input["new_daily_budget_brl"]
                    )
                elif tool_name == "analyze_performance":
                    result = _exec_analyze_performance(business_id)
                elif tool_name == "get_business_info":
                    result = _exec_get_business_info(business_id)
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
            except Exception as e:
                logger.error({"event": "luna_tool_error", "tool": tool_name, "error": str(e)})
                result = {"error": str(e)}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

        messages.append({"role": "user", "content": tool_results})

    final_text = next(
        (b.text for b in response.content if b.type == "text"),
        "Ação executada!"
    )
    if not ephemeral:
        _save_conversation(business_id, usuario_id, messages)
    return {"response": final_text, "message_count": len(messages)}

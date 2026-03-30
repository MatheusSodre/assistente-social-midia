import json
import logging
import os
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """
Você é um analista financeiro pessoal. Analise as transações bancárias abaixo dos últimos 30 dias e retorne insights úteis em português brasileiro.

Transações:
{transactions_json}

Retorne APENAS JSON válido, sem markdown, exatamente neste formato:
{{
  "summary": "Resumo executivo em 2-3 frases sobre os gastos do período",
  "top_categories": [
    {{"category": "nome da categoria", "total": 0.00, "count": 0, "percentage": 0.0}}
  ],
  "insights": [
    "Insight 1 sobre padrão de gastos",
    "Insight 2 sobre oportunidades de economia",
    "Insight 3 sobre tendências identificadas"
  ],
  "recommendations": [
    "Recomendação prática 1",
    "Recomendação prática 2",
    "Recomendação prática 3"
  ]
}}
"""


async def analyze_transactions(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    if not transactions:
        return {
            "summary": "Nenhuma transação encontrada para análise.",
            "top_categories": [],
            "insights": ["Conecte uma conta bancária para obter insights financeiros."],
            "recommendations": ["Adicione uma conta para começar a acompanhar seus gastos."],
        }

    # Prepara dados simplificados para o Claude (evita payload muito grande)
    simplified = [
        {
            "date": tx.get("date"),
            "description": tx.get("description"),
            "amount": tx.get("amount"),
            "type": tx.get("type"),
            "category": tx.get("category") or tx.get("categoryId"),
        }
        for tx in transactions[:200]  # limita a 200 transações
    ]

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = ANALYSIS_PROMPT.format(transactions_json=json.dumps(simplified, ensure_ascii=False, default=str))

    try:
        message = await client.messages.create(
            model="claude-sonnet-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Claude returned invalid JSON for finance analysis: %s", exc)
        return {
            "summary": "Análise temporariamente indisponível.",
            "top_categories": [],
            "insights": ["Tente novamente em alguns instantes."],
            "recommendations": [],
        }
    except Exception as exc:
        logger.error("Finance analysis error: %s", exc)
        raise

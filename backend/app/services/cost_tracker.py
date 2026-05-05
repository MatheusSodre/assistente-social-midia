"""
Calcula custo por chamada de modelo e persiste em mkt_agent_logs.
Tabela de preços hardcoded no MVP — quando precisar atualizar, edita aqui.
"""
import json
import math
from typing import Any
from uuid import UUID

import asyncpg

from app.core.db import tenant_context


# Preços em centavos USD por 1 milhão de tokens (input, output).
# Refs: https://www.anthropic.com/pricing
_LLM_PRICES_CENTS_PER_MTOK: dict[str, tuple[int, int]] = {
    "claude-sonnet-4": (300, 1500),    # $3 / $15 per MTok
    "claude-haiku-4":  (100, 500),     # $1 / $5 per MTok
    "claude-opus-4":   (1500, 7500),   # $15 / $75 per MTok
}

# Preço por imagem gerada (Gemini Flash Image / Nano Banana 2 ≈ $0.039).
_GEMINI_IMAGE_CENTS = 4


def calc_cost_cents(model: str, tokens_in: int, tokens_out: int) -> int:
    """Tabela de preços; modelo não-listado retorna 0 (sem barrar)."""
    lower = model.lower()
    if "gemini" in lower and "image" in lower:
        return _GEMINI_IMAGE_CENTS
    for prefix, (price_in, price_out) in _LLM_PRICES_CENTS_PER_MTOK.items():
        if prefix in lower:
            cents = (tokens_in * price_in + tokens_out * price_out) / 1_000_000
            return max(1, math.ceil(cents))  # nunca retorna 0 quando houve consumo
    return 0


class CostTrackerService:
    def __init__(self, pool: asyncpg.Pool, tenant_id: UUID) -> None:
        self._pool = pool
        self._tenant_id = tenant_id

    async def track(
        self,
        *,
        generation_id: UUID,
        agent_name: str,
        model: str,
        input: dict[str, Any],
        output: dict[str, Any],
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
    ) -> int:
        cost_cents = calc_cost_cents(model, tokens_in, tokens_out)

        async with tenant_context(self._pool, self._tenant_id) as conn:
            await conn.execute(
                """
                INSERT INTO mkt_agent_logs (
                    generation_id, agent_name, model,
                    input, output,
                    tokens_in, tokens_out, cost_cents, latency_ms
                ) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8, $9)
                """,
                generation_id,
                agent_name,
                model,
                json.dumps(input, default=str, ensure_ascii=False),
                json.dumps(output, default=str, ensure_ascii=False),
                tokens_in,
                tokens_out,
                cost_cents,
                latency_ms,
            )
            await conn.execute(
                """
                UPDATE mkt_generations
                   SET cost_cents = cost_cents + $1
                 WHERE id = $2
                """,
                cost_cents,
                generation_id,
            )

        return cost_cents

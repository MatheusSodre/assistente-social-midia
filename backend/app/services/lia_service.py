"""
CRUD de conversations e messages. Agente Lia (chat com tools) vem no PROMPT 04.5.
Aqui é só persistência: criar conversa, listar, salvar mensagem.
"""
import json
from typing import Any
from uuid import UUID

import asyncpg

from app.core.db import tenant_context
from app.models.lia import LiaConversation, LiaMessage, LiaMessageRole


class LiaService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    # ----------------------------------------------------- conversations
    async def list_conversations(
        self, *, tenant_id: UUID, limit: int = 20
    ) -> list[LiaConversation]:
        async with tenant_context(self._pool, tenant_id) as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM mkt_lia_conversations
                ORDER BY last_message_at DESC NULLS LAST
                LIMIT $1
                """,
                limit,
            )
        return [LiaConversation.model_validate(dict(r)) for r in rows]

    async def get_or_create_active(
        self, *, tenant_id: UUID, user_id: UUID
    ) -> LiaConversation:
        """Devolve a conversa ativa mais recente (não fechada) ou cria uma nova."""
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM mkt_lia_conversations
                WHERE closed_at IS NULL
                ORDER BY last_message_at DESC NULLS LAST
                LIMIT 1
                """
            )
            if row:
                return LiaConversation.model_validate(dict(row))

            row = await conn.fetchrow(
                """
                INSERT INTO mkt_lia_conversations (tenant_id, started_by_user_id)
                VALUES ($1, $2)
                RETURNING *
                """,
                tenant_id, user_id,
            )
        return LiaConversation.model_validate(dict(row))

    async def close_conversation(
        self, *, tenant_id: UUID, conversation_id: UUID, summary: str | None = None
    ) -> None:
        async with tenant_context(self._pool, tenant_id) as conn:
            await conn.execute(
                """
                UPDATE mkt_lia_conversations
                  SET closed_at = now(), summary = COALESCE($1, summary)
                  WHERE id = $2
                """,
                summary, conversation_id,
            )

    # ----------------------------------------------------------- messages
    async def list_messages(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        limit: int = 100,
    ) -> list[LiaMessage]:
        async with tenant_context(self._pool, tenant_id) as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM mkt_lia_messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                conversation_id, limit,
            )
        return [self._row_to_msg(r) for r in rows]

    async def append_message(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        role: LiaMessageRole,
        content: str | None = None,
        tool_name: str | None = None,
        tool_input: dict[str, Any] | None = None,
        tool_use_id: str | None = None,
        tool_result: dict[str, Any] | None = None,
        model: str | None = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost_cents: int = 0,
        latency_ms: int | None = None,
    ) -> LiaMessage:
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO mkt_lia_messages (
                  conversation_id, role, content,
                  tool_name, tool_input, tool_use_id, tool_result,
                  model, tokens_in, tokens_out, cost_cents, latency_ms
                ) VALUES (
                  $1, $2, $3, $4, $5::jsonb, $6, $7::jsonb, $8, $9, $10, $11, $12
                )
                RETURNING *
                """,
                conversation_id, role.value, content,
                tool_name,
                json.dumps(tool_input, default=str) if tool_input else None,
                tool_use_id,
                json.dumps(tool_result, default=str) if tool_result else None,
                model, tokens_in, tokens_out, cost_cents, latency_ms,
            )

            await conn.execute(
                """
                UPDATE mkt_lia_conversations
                  SET message_count = message_count + 1,
                      total_cost_cents = total_cost_cents + $1,
                      last_message_at = now()
                  WHERE id = $2
                """,
                cost_cents, conversation_id,
            )

        return self._row_to_msg(row)

    @staticmethod
    def _row_to_msg(row) -> LiaMessage:
        data = dict(row)
        for jsonb_field in ("tool_input", "tool_result"):
            v = data.get(jsonb_field)
            if isinstance(v, str):
                data[jsonb_field] = json.loads(v)
        return LiaMessage.model_validate(data)

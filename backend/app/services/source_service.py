"""CRUD de fontes. Worker de processamento real vem no PROMPT 05."""
import json
from uuid import UUID

import asyncpg

from app.core.db import tenant_context
from app.models.source import Source, SourceCreate


class SourceService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def list_all(self, *, tenant_id: UUID) -> list[Source]:
        async with tenant_context(self._pool, tenant_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM mkt_sources ORDER BY created_at DESC"
            )
        return [self._row_to_model(r) for r in rows]

    async def create(
        self,
        *,
        tenant_id: UUID,
        added_by_user_id: UUID,
        payload: SourceCreate,
    ) -> Source:
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO mkt_sources (
                  tenant_id, type, name, url_or_path,
                  status, added_by_user_id, added_via_chat
                )
                VALUES ($1, $2, $3, $4, 'pending', $5, $6)
                RETURNING *
                """,
                tenant_id, payload.type.value, payload.name, payload.url_or_path,
                added_by_user_id, payload.added_via_chat,
            )
        return self._row_to_model(row)

    async def delete(self, *, tenant_id: UUID, source_id: UUID) -> bool:
        async with tenant_context(self._pool, tenant_id) as conn:
            result = await conn.execute("DELETE FROM mkt_sources WHERE id = $1", source_id)
        return result.endswith(" 1")

    async def reindex(self, *, tenant_id: UUID, source_id: UUID) -> Source | None:
        """Marca pra reprocessar — worker pega depois."""
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                """
                UPDATE mkt_sources
                  SET status = 'pending', error_message = NULL
                  WHERE id = $1
                  RETURNING *
                """,
                source_id,
            )
        return self._row_to_model(row) if row else None

    @staticmethod
    def _row_to_model(row) -> Source:
        data = dict(row)
        v = data.get("metadata")
        if isinstance(v, str):
            data["metadata"] = json.loads(v)
        if data.get("metadata") is None:
            data["metadata"] = {}
        return Source.model_validate(data)

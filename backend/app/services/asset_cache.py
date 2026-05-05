"""
Cache de imagens: lookup/save em mkt_assets via RLS de tenant_context.

A policy mkt_assets_select já restringe ao tenant via JOIN em mkt_generations,
então o SELECT abaixo só vê assets do tenant atual sem precisar JOIN explícito.
"""
import json
from typing import Any
from uuid import UUID

import asyncpg

from app.core.db import tenant_context


class AssetCacheService:
    def __init__(self, pool: asyncpg.Pool, tenant_id: UUID) -> None:
        self._pool = pool
        self._tenant_id = tenant_id

    async def lookup(self, *, cache_hash: str, tenant_id: UUID) -> str | None:
        # tenant_id passado pelo Visual Agent (interface uniforme), mas o
        # filtro real vem da RLS policy via tenant_context — devem coincidir.
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                """
                SELECT storage_path
                  FROM mkt_assets
                 WHERE type = 'image_png'
                   AND metadata->>'cache_hash' = $1
                 ORDER BY created_at DESC
                 LIMIT 1
                """,
                cache_hash,
            )
        return row["storage_path"] if row else None

    async def save(
        self,
        *,
        generation_id: UUID,
        cache_hash: str,
        storage_path: str,
        metadata: dict[str, Any],
    ) -> None:
        async with tenant_context(self._pool, self._tenant_id) as conn:
            await conn.execute(
                """
                INSERT INTO mkt_assets (generation_id, type, storage_path, metadata)
                VALUES ($1, 'image_png', $2, $3::jsonb)
                """,
                generation_id,
                storage_path,
                json.dumps(metadata, default=str, ensure_ascii=False),
            )

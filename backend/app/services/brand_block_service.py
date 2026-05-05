"""
CRUD dos 7 blocos. Toda escrita passa por pending_change — exceto:
- bootstrap inicial (criar bloco vazio se não existe)
- aceite de pending_change (cria nova version, atualiza ponteiro)
"""
import json
from typing import Any
from uuid import UUID

import asyncpg
from fastapi import HTTPException

from app.core.db import tenant_context
from app.models.brand_block import (
    BlockKey,
    BlockStatus,
    BrandBlock,
    BrandBlockVersion,
    BrandMemoryDashboard,
    ChangeSourceType,
    validate_block_content,
)


_BLOCK_KEY_ORDER = [
    BlockKey.BRAND, BlockKey.ICP, BlockKey.TONE, BlockKey.VISUAL,
    BlockKey.TOPICS, BlockKey.COMPETITORS, BlockKey.EXAMPLES,
]


class BrandBlockService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    # -------------------------------------------------------------- dashboard
    async def get_dashboard(self, *, tenant_id: UUID) -> BrandMemoryDashboard:
        await self._ensure_blocks_exist(tenant_id=tenant_id)

        async with tenant_context(self._pool, tenant_id) as conn:
            block_rows = await conn.fetch(
                """
                SELECT
                  b.id, b.tenant_id, b.block_key, b.current_version_id,
                  b.status, b.confidence, b.source_label,
                  b.created_at, b.updated_at,
                  v.content, v.version_number
                FROM mkt_brand_blocks b
                LEFT JOIN mkt_brand_block_versions v ON v.id = b.current_version_id
                WHERE b.tenant_id = $1
                ORDER BY array_position(
                  ARRAY['brand','icp','tone','visual','topics','competitors','examples']::mkt_brand_block_key[],
                  b.block_key
                )
                """,
                tenant_id,
            )
            pending_count_row = await conn.fetchrow(
                "SELECT count(*) AS n FROM mkt_pending_changes WHERE status = 'pending'"
            )

        blocks = [self._row_to_block(r) for r in block_rows]
        total_conf = sum(b.confidence for b in blocks)
        completion = round(total_conf / len(blocks)) if blocks else 0

        return BrandMemoryDashboard(
            blocks=blocks,
            completion_pct=completion,
            pending_changes_count=pending_count_row["n"],
        )

    async def get_block(
        self, *, tenant_id: UUID, block_key: BlockKey
    ) -> BrandBlock | None:
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                """
                SELECT b.id, b.tenant_id, b.block_key, b.current_version_id,
                       b.status, b.confidence, b.source_label,
                       b.created_at, b.updated_at,
                       v.content, v.version_number
                FROM mkt_brand_blocks b
                LEFT JOIN mkt_brand_block_versions v ON v.id = b.current_version_id
                WHERE b.block_key = $1
                """,
                block_key.value,
            )
        return self._row_to_block(row) if row else None

    # -------------------------------------------------------- escrita direta
    # SÓ usar em casos onde não cabe pending_change (bootstrap, accept de change).
    # Endpoint público de PATCH NÃO usa isso — usa propose_change.
    async def apply_version_internal(
        self,
        *,
        tenant_id: UUID,
        block_key: BlockKey,
        content: dict[str, Any],
        source_type: ChangeSourceType,
        source_ref: str | None = None,
        created_by: UUID | None = None,
        created_by_agent: str | None = None,
        reason: str | None = None,
    ) -> BrandBlockVersion:
        validated = validate_block_content(block_key, content)
        new_status, new_confidence = self._infer_status_and_confidence(block_key, validated)

        async with tenant_context(self._pool, tenant_id) as conn:
            # garante bloco existe
            block_row = await conn.fetchrow(
                "SELECT id FROM mkt_brand_blocks WHERE block_key = $1",
                block_key.value,
            )
            if not block_row:
                block_row = await conn.fetchrow(
                    """
                    INSERT INTO mkt_brand_blocks (tenant_id, block_key, status, confidence)
                    VALUES ($1, $2, 'empty', 0)
                    RETURNING id
                    """,
                    tenant_id, block_key.value,
                )

            block_id = block_row["id"]

            # próximo version_number
            next_v = await conn.fetchval(
                """
                SELECT COALESCE(MAX(version_number), 0) + 1
                FROM mkt_brand_block_versions WHERE block_id = $1
                """,
                block_id,
            )

            version_row = await conn.fetchrow(
                """
                INSERT INTO mkt_brand_block_versions (
                  block_id, version_number, content,
                  source_type, source_ref, created_by, created_by_agent, reason
                ) VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, $8)
                RETURNING *
                """,
                block_id, next_v, json.dumps(validated, default=str),
                source_type.value, source_ref, created_by, created_by_agent, reason,
            )

            await conn.execute(
                """
                UPDATE mkt_brand_blocks
                  SET current_version_id = $1, status = $2, confidence = $3
                  WHERE id = $4
                """,
                version_row["id"], new_status.value, new_confidence, block_id,
            )

        return BrandBlockVersion.model_validate({
            **dict(version_row),
            "content": json.loads(version_row["content"])
                       if isinstance(version_row["content"], str)
                       else version_row["content"],
        })

    # ----------------------------------------------------- versions history
    async def list_versions(
        self, *, tenant_id: UUID, block_key: BlockKey, limit: int = 50
    ) -> list[BrandBlockVersion]:
        async with tenant_context(self._pool, tenant_id) as conn:
            rows = await conn.fetch(
                """
                SELECT v.*
                FROM mkt_brand_block_versions v
                JOIN mkt_brand_blocks b ON b.id = v.block_id
                WHERE b.block_key = $1
                ORDER BY v.version_number DESC
                LIMIT $2
                """,
                block_key.value, limit,
            )
        return [
            BrandBlockVersion.model_validate({
                **dict(r),
                "content": json.loads(r["content"]) if isinstance(r["content"], str) else r["content"],
            })
            for r in rows
        ]

    async def revert_to_version(
        self, *, tenant_id: UUID, block_key: BlockKey, version_number: int
    ) -> BrandBlock:
        async with tenant_context(self._pool, tenant_id) as conn:
            target = await conn.fetchrow(
                """
                SELECT v.id, v.content
                FROM mkt_brand_block_versions v
                JOIN mkt_brand_blocks b ON b.id = v.block_id
                WHERE b.block_key = $1 AND v.version_number = $2
                """,
                block_key.value, version_number,
            )
            if not target:
                raise HTTPException(404, f"version {version_number} not found")

        # Cria nova version (não troca o ponteiro pra preservar histórico)
        target_content = (
            target["content"] if isinstance(target["content"], dict)
            else json.loads(target["content"])
        )
        await self.apply_version_internal(
            tenant_id=tenant_id,
            block_key=block_key,
            content=target_content,
            source_type=ChangeSourceType.MANUAL,
            source_ref=f"revert from v{version_number}",
            reason=f"reverted to v{version_number}",
        )

        block = await self.get_block(tenant_id=tenant_id, block_key=block_key)
        if not block:
            raise HTTPException(500, "block missing after revert")
        return block

    # ----------------------------------------------------------- helpers
    async def _ensure_blocks_exist(self, *, tenant_id: UUID) -> None:
        """Garante que tenant tem 7 linhas em mkt_brand_blocks (vazias se primeira vez)."""
        async with tenant_context(self._pool, tenant_id) as conn:
            existing = await conn.fetch(
                "SELECT block_key FROM mkt_brand_blocks WHERE tenant_id = $1",
                tenant_id,
            )
            existing_keys = {r["block_key"] for r in existing}
            missing = [k for k in _BLOCK_KEY_ORDER if k.value not in existing_keys]

            for block_key in missing:
                await conn.execute(
                    """
                    INSERT INTO mkt_brand_blocks (tenant_id, block_key, status, confidence)
                    VALUES ($1, $2, 'empty', 0)
                    ON CONFLICT (tenant_id, block_key) DO NOTHING
                    """,
                    tenant_id, block_key.value,
                )

    @staticmethod
    def _infer_status_and_confidence(
        block_key: BlockKey, content: dict[str, Any]
    ) -> tuple[BlockStatus, int]:
        """Heurística simples por bloco — pode ficar mais sofisticada depois."""
        if not content or all(_is_empty(v) for v in content.values()):
            return BlockStatus.EMPTY, 0

        # Bloco completo se todos os campos importantes preenchidos
        if block_key == BlockKey.BRAND:
            ok = bool(content.get("name")) and bool(content.get("positioning"))
            return (BlockStatus.PARTIAL, 70) if ok else (BlockStatus.PARTIAL, 40)
        if block_key == BlockKey.ICP:
            personas = content.get("personas", [])
            if len(personas) == 0:
                return BlockStatus.EMPTY, 0
            has_pains = all(p.get("pains") for p in personas)
            return (BlockStatus.COMPLETE, 90) if has_pains else (BlockStatus.PARTIAL, 60)
        if block_key == BlockKey.TONE:
            ok = bool(content.get("style")) and len(content.get("do", [])) > 0
            return (BlockStatus.COMPLETE, 85) if ok else (BlockStatus.PARTIAL, 50)
        if block_key == BlockKey.VISUAL:
            ok = bool(content.get("primary_color"))
            return (BlockStatus.PARTIAL, 80) if ok else (BlockStatus.PARTIAL, 30)
        if block_key == BlockKey.TOPICS:
            n = len(content.get("pillars", []))
            if n >= 4:
                return BlockStatus.COMPLETE, 85
            if n > 0:
                return BlockStatus.PARTIAL, 60
            return BlockStatus.EMPTY, 0
        if block_key == BlockKey.COMPETITORS:
            n = len(content.get("items", []))
            if n >= 3:
                return BlockStatus.COMPLETE, 80
            if n > 0:
                return BlockStatus.PARTIAL, 50
            return BlockStatus.EMPTY, 0
        if block_key == BlockKey.EXAMPLES:
            n = len(content.get("items", []))
            if n >= 3:
                return BlockStatus.COMPLETE, 75
            if n > 0:
                return BlockStatus.PARTIAL, 45
            return BlockStatus.EMPTY, 0
        return BlockStatus.PARTIAL, 50

    @staticmethod
    def _row_to_block(row) -> BrandBlock:
        data = dict(row)
        c = data.get("content")
        if isinstance(c, str):
            data["content"] = json.loads(c)
        return BrandBlock.model_validate(data)


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, (str, list, dict)):
        return len(v) == 0
    return False

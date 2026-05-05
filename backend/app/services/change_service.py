"""
Orquestra pending changes: criar, aceitar, rejeitar.
Aceitar = aplicar version + gerar cascade hints.
"""
import json
from typing import Any
from uuid import UUID

import asyncpg
from fastapi import HTTPException

from app.core.db import tenant_context
from app.models.brand_block import BlockKey, validate_block_content
from app.models.pending_change import (
    CascadeHint,
    PendingChange,
    PendingChangeCreate,
    PendingChangeStatus,
)
from app.services.brand_block_service import BrandBlockService


class ChangeService:
    def __init__(self, pool: asyncpg.Pool, block_service: BrandBlockService) -> None:
        self._pool = pool
        self._block_service = block_service

    # ---------------------------------------------------------- propose
    async def propose(
        self,
        *,
        tenant_id: UUID,
        proposed_by_user_id: UUID | None,
        payload: PendingChangeCreate,
    ) -> PendingChange:
        # valida content contra schema do bloco
        validated_content = validate_block_content(payload.block_key, payload.proposed_content)

        async with tenant_context(self._pool, tenant_id) as conn:
            block_row = await conn.fetchrow(
                "SELECT id, current_version_id FROM mkt_brand_blocks WHERE block_key = $1",
                payload.block_key.value,
            )
            if not block_row:
                # garante bloco existe
                await self._block_service._ensure_blocks_exist(tenant_id=tenant_id)
                block_row = await conn.fetchrow(
                    "SELECT id, current_version_id FROM mkt_brand_blocks WHERE block_key = $1",
                    payload.block_key.value,
                )

            cascades = await self._compute_cascade_hints(
                conn, payload.block_key, validated_content
            )

            row = await conn.fetchrow(
                """
                INSERT INTO mkt_pending_changes (
                  tenant_id, block_id, proposed_by_user_id, proposed_by_agent,
                  source_type, source_label, source_ref,
                  from_version_id, proposed_content, reason, cascades
                ) VALUES (
                  $1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11::jsonb
                )
                RETURNING *
                """,
                tenant_id, block_row["id"], proposed_by_user_id, payload.proposed_by_agent,
                payload.source_type.value, payload.source_label, payload.source_ref,
                block_row["current_version_id"],
                json.dumps(validated_content, default=str),
                payload.reason,
                json.dumps([c.model_dump() for c in cascades], default=str),
            )

        return await self.get(tenant_id=tenant_id, change_id=row["id"])

    # ---------------------------------------------------------- get/list
    async def get(self, *, tenant_id: UUID, change_id: UUID) -> PendingChange:
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                """
                SELECT
                  pc.*,
                  b.block_key,
                  vfrom.version_number AS from_version_number,
                  vfrom.content AS from_content
                FROM mkt_pending_changes pc
                JOIN mkt_brand_blocks b ON b.id = pc.block_id
                LEFT JOIN mkt_brand_block_versions vfrom ON vfrom.id = pc.from_version_id
                WHERE pc.id = $1
                """,
                change_id,
            )
        if not row:
            raise HTTPException(404, "change not found")
        return self._row_to_model(row)

    async def list_pending(self, *, tenant_id: UUID) -> list[PendingChange]:
        async with tenant_context(self._pool, tenant_id) as conn:
            rows = await conn.fetch(
                """
                SELECT
                  pc.*,
                  b.block_key,
                  vfrom.version_number AS from_version_number,
                  vfrom.content AS from_content
                FROM mkt_pending_changes pc
                JOIN mkt_brand_blocks b ON b.id = pc.block_id
                LEFT JOIN mkt_brand_block_versions vfrom ON vfrom.id = pc.from_version_id
                WHERE pc.status = 'pending'
                ORDER BY pc.created_at DESC
                """
            )
        return [self._row_to_model(r) for r in rows]

    # ---------------------------------------------------------- accept
    async def accept(
        self, *, tenant_id: UUID, change_id: UUID, resolved_by_user_id: UUID
    ) -> PendingChange:
        change = await self.get(tenant_id=tenant_id, change_id=change_id)
        if change.status != PendingChangeStatus.PENDING:
            raise HTTPException(409, f"change already {change.status.value}")

        await self._block_service.apply_version_internal(
            tenant_id=tenant_id,
            block_key=change.block_key,
            content=change.proposed_content,
            source_type=change.source_type,
            source_ref=str(change.id),
            created_by=resolved_by_user_id,
            created_by_agent=change.proposed_by_agent,
            reason=change.reason,
        )

        async with tenant_context(self._pool, tenant_id) as conn:
            await conn.execute(
                """
                UPDATE mkt_pending_changes
                  SET status = 'accepted',
                      resolved_by_user_id = $1,
                      resolved_at = now()
                  WHERE id = $2
                """,
                resolved_by_user_id, change_id,
            )

            # Cria pending_changes filhas pra cascades — usa source_type='cascade'.
            # Cascade não muda content automaticamente — só registra a hint.
            # Lia/Vega usam isso pra propor uma sub-mudança em sequência.
            for cascade in change.cascades:
                target_block = await conn.fetchrow(
                    """
                    SELECT v.content FROM mkt_brand_blocks b
                    LEFT JOIN mkt_brand_block_versions v ON v.id = b.current_version_id
                    WHERE b.block_key = $1
                    """,
                    cascade.block_key.value,
                )
                if not target_block or target_block["content"] is None:
                    continue
                await conn.execute(
                    """
                    INSERT INTO mkt_pending_changes (
                      tenant_id, block_id,
                      proposed_by_agent, source_type, source_label, source_ref,
                      from_version_id, proposed_content, reason, cascades
                    )
                    SELECT
                      $1, b.id,
                      'cascade', 'cascade', 'cascade · ' || $2, $3,
                      b.current_version_id, v.content, $4, '[]'::jsonb
                    FROM mkt_brand_blocks b
                    LEFT JOIN mkt_brand_block_versions v ON v.id = b.current_version_id
                    WHERE b.block_key = $5
                    """,
                    tenant_id,
                    change.block_key.value,
                    str(change.id),
                    cascade.hint[:200],
                    cascade.block_key.value,
                )

        return await self.get(tenant_id=tenant_id, change_id=change_id)

    # ---------------------------------------------------------- reject
    async def reject(
        self, *, tenant_id: UUID, change_id: UUID, resolved_by_user_id: UUID
    ) -> PendingChange:
        async with tenant_context(self._pool, tenant_id) as conn:
            await conn.execute(
                """
                UPDATE mkt_pending_changes
                  SET status = 'rejected',
                      resolved_by_user_id = $1,
                      resolved_at = now()
                  WHERE id = $2 AND status = 'pending'
                """,
                resolved_by_user_id, change_id,
            )
        return await self.get(tenant_id=tenant_id, change_id=change_id)

    # ---------------------------------------------------------- cascades
    async def _compute_cascade_hints(
        self,
        conn: asyncpg.Connection,
        block_key: BlockKey,
        new_content: dict[str, Any],
    ) -> list[CascadeHint]:
        """Lookup em mkt_change_cascades. Triggers refinados depois."""
        rows = await conn.fetch(
            """
            SELECT suggested_block_key, suggestion_template
            FROM mkt_change_cascades
            WHERE trigger_block_key = $1 AND enabled = true
            """,
            block_key.value,
        )
        return [
            CascadeHint(
                block_key=BlockKey(r["suggested_block_key"]),
                hint=r["suggestion_template"],
            )
            for r in rows
        ]

    @staticmethod
    def _row_to_model(row) -> PendingChange:
        data = dict(row)
        for jsonb_field in ("proposed_content", "from_content", "cascades"):
            v = data.get(jsonb_field)
            if isinstance(v, str):
                data[jsonb_field] = json.loads(v)
        if "cascades" not in data or data["cascades"] is None:
            data["cascades"] = []
        return PendingChange.model_validate(data)

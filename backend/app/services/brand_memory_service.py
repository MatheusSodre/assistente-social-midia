import json
from uuid import UUID

import asyncpg

from app.core.db import tenant_context
from app.models.brand_memory import (
    BrandMemory,
    BrandMemoryCreate,
    BrandMemoryUpdate,
)


class BrandMemoryService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def list_all(self, *, tenant_id: UUID) -> list[BrandMemory]:
        async with tenant_context(self._pool, tenant_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM mkt_brand_memory ORDER BY created_at DESC"
            )
        return [self._row_to_model(r) for r in rows]

    async def get(self, *, tenant_id: UUID, brand_id: UUID) -> BrandMemory | None:
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                "SELECT * FROM mkt_brand_memory WHERE id = $1", brand_id
            )
        return self._row_to_model(row) if row else None

    async def create(
        self, *, tenant_id: UUID, payload: BrandMemoryCreate
    ) -> BrandMemory:
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO mkt_brand_memory (
                    tenant_id, name, positioning,
                    icp, tone_of_voice, visual_identity,
                    pillars, competitors, examples
                ) VALUES (
                    $1, $2, $3,
                    $4::jsonb, $5::jsonb, $6::jsonb,
                    $7, $8::jsonb, $9::jsonb
                )
                RETURNING *
                """,
                tenant_id,
                payload.name,
                payload.positioning,
                json.dumps([p.model_dump() for p in payload.icp]),
                payload.tone_of_voice.model_dump_json(),
                payload.visual_identity.model_dump_json(),
                payload.pillars,
                json.dumps([c.model_dump() for c in payload.competitors]),
                json.dumps([e.model_dump() for e in payload.examples]),
            )
        return self._row_to_model(row)

    async def update(
        self, *, tenant_id: UUID, brand_id: UUID, payload: BrandMemoryUpdate
    ) -> BrandMemory | None:
        fields, values = self._build_update_fields(payload)
        if not fields:
            return await self.get(tenant_id=tenant_id, brand_id=brand_id)

        sets = ", ".join(f"{name} = ${i + 1}" for i, (name, _cast) in enumerate(fields))
        casts = {name: cast for name, cast in fields}
        # apply cast suffix
        sets = ", ".join(
            f"{name} = ${i + 1}{casts[name]}"
            for i, (name, _) in enumerate(fields)
        )

        sql = f"UPDATE mkt_brand_memory SET {sets} WHERE id = ${len(fields) + 1} RETURNING *"
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(sql, *values, brand_id)
        return self._row_to_model(row) if row else None

    async def delete(self, *, tenant_id: UUID, brand_id: UUID) -> bool:
        async with tenant_context(self._pool, tenant_id) as conn:
            result = await conn.execute(
                "DELETE FROM mkt_brand_memory WHERE id = $1", brand_id
            )
        return result.endswith(" 1")

    # -------------------------------------------------------- helpers
    @staticmethod
    def _build_update_fields(
        payload: BrandMemoryUpdate,
    ) -> tuple[list[tuple[str, str]], list]:
        """Retorna (lista de (col, cast_suffix), lista de valores)."""
        fields: list[tuple[str, str]] = []
        values: list = []

        if payload.name is not None:
            fields.append(("name", "")); values.append(payload.name)
        if payload.positioning is not None:
            fields.append(("positioning", "")); values.append(payload.positioning)
        if payload.icp is not None:
            fields.append(("icp", "::jsonb"))
            values.append(json.dumps([p.model_dump() for p in payload.icp]))
        if payload.tone_of_voice is not None:
            fields.append(("tone_of_voice", "::jsonb"))
            values.append(payload.tone_of_voice.model_dump_json())
        if payload.visual_identity is not None:
            fields.append(("visual_identity", "::jsonb"))
            values.append(payload.visual_identity.model_dump_json())
        if payload.pillars is not None:
            fields.append(("pillars", "")); values.append(payload.pillars)
        if payload.competitors is not None:
            fields.append(("competitors", "::jsonb"))
            values.append(json.dumps([c.model_dump() for c in payload.competitors]))
        if payload.examples is not None:
            fields.append(("examples", "::jsonb"))
            values.append(json.dumps([e.model_dump() for e in payload.examples]))
        return fields, values

    @staticmethod
    def _row_to_model(row) -> BrandMemory:
        data = dict(row)
        for jsonb_field in ("icp", "tone_of_voice", "visual_identity", "competitors", "examples"):
            v = data.get(jsonb_field)
            if isinstance(v, str):
                data[jsonb_field] = json.loads(v)
        return BrandMemory.model_validate(data)

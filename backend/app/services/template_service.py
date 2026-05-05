import json
from uuid import UUID

import asyncpg

from app.core.db import tenant_context
from app.models.template import Template


class TemplateService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def list_all(self, *, tenant_id: UUID) -> list[Template]:
        async with tenant_context(self._pool, tenant_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM mkt_templates ORDER BY name"
            )
        return [self._row_to_model(r) for r in rows]

    async def get(self, *, tenant_id: UUID, template_id: UUID) -> Template | None:
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                "SELECT * FROM mkt_templates WHERE id = $1", template_id
            )
        return self._row_to_model(row) if row else None

    @staticmethod
    def _row_to_model(row) -> Template:
        data = dict(row)
        for jsonb_field in ("dimensions", "slots", "layout_config"):
            v = data.get(jsonb_field)
            if isinstance(v, str):
                data[jsonb_field] = json.loads(v)
        return Template.model_validate(data)

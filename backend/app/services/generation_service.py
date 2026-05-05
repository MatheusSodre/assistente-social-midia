import json
import logging
from uuid import UUID

import asyncpg

from app.agents.orchestrator import OrchestratorAgent
from app.core.db import tenant_context
from app.models.brand_memory import BrandMemory
from app.models.generation import Generation, GenerationResult, GenerationStatus
from app.models.template import Template
from app.services.brand_memory_service import BrandMemoryService
from app.services.template_service import TemplateService


logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(
        self,
        *,
        pool: asyncpg.Pool,
        brand_service: BrandMemoryService,
        template_service: TemplateService,
        orchestrator_factory,  # callable(tenant_id) -> OrchestratorAgent
    ) -> None:
        self._pool = pool
        self._brand_service = brand_service
        self._template_service = template_service
        self._orchestrator_factory = orchestrator_factory

    # --------------------------------------------------------- create / list
    async def create(
        self,
        *,
        tenant_id: UUID,
        created_by: UUID,
        brief: str,
        template_id: UUID | None,
    ) -> UUID:
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO mkt_generations (tenant_id, brief, template_id, created_by, status)
                VALUES ($1, $2, $3, $4, 'pending')
                RETURNING id
                """,
                tenant_id, brief, template_id, created_by,
            )
        return row["id"]

    async def get(self, *, tenant_id: UUID, generation_id: UUID) -> Generation | None:
        async with tenant_context(self._pool, tenant_id) as conn:
            row = await conn.fetchrow(
                "SELECT * FROM mkt_generations WHERE id = $1", generation_id
            )
        return self._row_to_model(row) if row else None

    async def list_all(self, *, tenant_id: UUID, limit: int = 50) -> list[Generation]:
        async with tenant_context(self._pool, tenant_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM mkt_generations ORDER BY created_at DESC LIMIT $1",
                limit,
            )
        return [self._row_to_model(r) for r in rows]

    # ----------------------------------------------------------- background
    async def run_pipeline(self, *, generation_id: UUID, tenant_id: UUID) -> None:
        """
        Roda em BackgroundTask. Carrega brand+template, chama orchestrator,
        atualiza status a cada etapa via NOTIFY, persiste resultado final.
        """
        try:
            generation = await self.get(tenant_id=tenant_id, generation_id=generation_id)
            if generation is None:
                logger.error(
                    "generation not found",
                    extra={"generation_id": str(generation_id)},
                )
                return

            brand = await self._load_brand(tenant_id=tenant_id)
            template = await self._load_template(
                tenant_id=tenant_id, template_id=generation.template_id
            )

            orchestrator: OrchestratorAgent = self._orchestrator_factory(tenant_id)

            async def set_status(status: GenerationStatus) -> None:
                await self._update_status(
                    tenant_id=tenant_id,
                    generation_id=generation_id,
                    status=status,
                )

            result = await orchestrator.run(
                brief=generation.brief,
                brand=brand,
                template=template,
                generation_id=generation_id,
                tenant_id=tenant_id,
                set_status=set_status,
            )

            await self._mark_done(
                tenant_id=tenant_id, generation_id=generation_id, result=result
            )

        except Exception as exc:
            logger.exception(
                "pipeline failed",
                extra={"generation_id": str(generation_id)},
            )
            await self._mark_failed(
                tenant_id=tenant_id,
                generation_id=generation_id,
                error=f"{type(exc).__name__}: {exc}",
            )

    # ----------------------------------------------------------- internals
    async def _load_brand(self, *, tenant_id: UUID) -> BrandMemory:
        brands = await self._brand_service.list_all(tenant_id=tenant_id)
        if not brands:
            raise RuntimeError("Tenant não tem Brand Memory cadastrada")
        return brands[0]  # MVP: 1 brand por tenant; pega a mais recente

    async def _load_template(
        self, *, tenant_id: UUID, template_id: UUID | None
    ) -> Template:
        if template_id is None:
            templates = await self._template_service.list_all(tenant_id=tenant_id)
            if not templates:
                raise RuntimeError("Sem templates disponíveis")
            return templates[0]
        template = await self._template_service.get(
            tenant_id=tenant_id, template_id=template_id
        )
        if template is None:
            raise RuntimeError(f"Template {template_id} não encontrado")
        return template

    async def _update_status(
        self, *, tenant_id: UUID, generation_id: UUID, status: GenerationStatus
    ) -> None:
        async with tenant_context(self._pool, tenant_id) as conn:
            await conn.execute(
                "UPDATE mkt_generations SET status = $1 WHERE id = $2",
                status.value, generation_id,
            )
            await conn.execute(
                "SELECT pg_notify($1, $2)",
                f"generation_{generation_id}",
                json.dumps({"status": status.value}),
            )

    async def _mark_done(
        self,
        *,
        tenant_id: UUID,
        generation_id: UUID,
        result: GenerationResult,
    ) -> None:
        async with tenant_context(self._pool, tenant_id) as conn:
            await conn.execute(
                """
                UPDATE mkt_generations
                   SET status = 'done',
                       result = $1::jsonb,
                       completed_at = now()
                 WHERE id = $2
                """,
                result.model_dump_json(),
                generation_id,
            )
            await conn.execute(
                "SELECT pg_notify($1, $2)",
                f"generation_{generation_id}",
                json.dumps({"status": "done"}),
            )

    async def _mark_failed(
        self, *, tenant_id: UUID, generation_id: UUID, error: str
    ) -> None:
        async with tenant_context(self._pool, tenant_id) as conn:
            await conn.execute(
                """
                UPDATE mkt_generations
                   SET status = 'failed',
                       result = jsonb_set(coalesce(result, '{}'::jsonb), '{error}', to_jsonb($1::text)),
                       completed_at = now()
                 WHERE id = $2
                """,
                error, generation_id,
            )
            await conn.execute(
                "SELECT pg_notify($1, $2)",
                f"generation_{generation_id}",
                json.dumps({"status": "failed", "error": error}),
            )

    @staticmethod
    def _row_to_model(row) -> Generation:
        data = dict(row)
        result_raw = data.get("result")
        if isinstance(result_raw, str):
            data["result"] = json.loads(result_raw)
        return Generation.model_validate(data)

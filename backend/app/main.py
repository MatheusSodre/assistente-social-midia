from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents import build_orchestrator
from app.agents.orchestrator import OrchestratorAgent
from app.api.assets import router as assets_router
from app.api.brand_blocks import router as brand_blocks_router
from app.api.brand_memory import router as brand_memory_router
from app.api.changes import router as changes_router
from app.api.generations import router as generations_router
from app.api.lia import router as lia_router
from app.api.sources import router as sources_router
from app.api.templates import router as templates_router
from app.core.config import get_settings
from app.core.db import close_pool, create_pool
from app.core.logging import configure_logging
from app.integrations.supabase_client import (
    SupabaseStorage,
    build_supabase_admin_client,
)
from app.services.asset_cache import AssetCacheService
from app.services.brand_block_service import BrandBlockService
from app.services.brand_memory_service import BrandMemoryService
from app.services.change_service import ChangeService
from app.services.cost_tracker import CostTrackerService
from app.services.generation_service import GenerationService
from app.services.lia_service import LiaService
from app.services.source_service import SourceService
from app.services.storage_service import StorageService
from app.services.template_service import TemplateService


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    pool = await create_pool()

    storage_client = SupabaseStorage(build_supabase_admin_client(settings))
    storage_service = StorageService(storage_client)
    brand_service = BrandMemoryService(pool)
    template_service = TemplateService(pool)

    brand_block_service = BrandBlockService(pool)
    change_service = ChangeService(pool, brand_block_service)
    source_service = SourceService(pool)
    lia_service = LiaService(pool)

    def orchestrator_factory(tenant_id: UUID) -> OrchestratorAgent:
        cost_tracker = CostTrackerService(pool, tenant_id)
        asset_cache = AssetCacheService(pool, tenant_id)
        return build_orchestrator(
            settings=settings,
            cost_tracker=cost_tracker,
            asset_cache=asset_cache,
        )

    generation_service = GenerationService(
        pool=pool,
        brand_service=brand_service,
        template_service=template_service,
        orchestrator_factory=orchestrator_factory,
    )

    app.state.settings = settings
    app.state.pool = pool
    app.state.storage_service = storage_service
    app.state.brand_service = brand_service
    app.state.template_service = template_service
    app.state.generation_service = generation_service
    app.state.brand_block_service = brand_block_service
    app.state.change_service = change_service
    app.state.source_service = source_service
    app.state.lia_service = lia_service

    yield

    await close_pool()


app = FastAPI(
    title="Assistente Social Media",
    description="Geração de marketing para Instagram via agentes IA",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Brand-memory novo (governance) registrado ANTES do antigo pra que GET ""
# devolva BrandMemoryDashboard. Endpoints antigos com /{brand_id} ficam
# acessíveis mas marcados deprecated — saem no fim do Sprint 3.
app.include_router(brand_blocks_router)
app.include_router(brand_memory_router, deprecated=True)
app.include_router(changes_router)
app.include_router(sources_router)
app.include_router(lia_router)
app.include_router(templates_router)
app.include_router(generations_router)
app.include_router(assets_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "assistente-social-media"}

from app.agents.brand_agent import BrandAgent
from app.agents.content_agent import ContentAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.protocols import AssetCache, CostTracker
from app.agents.visual_agent import VisualAgent
from app.core.config import Settings
from app.integrations.anthropic_client import AnthropicLLMProvider
from app.integrations.gemini_client import GeminiImageProvider
from app.integrations.supabase_client import SupabaseStorage, build_supabase_admin_client


def build_orchestrator(
    *,
    settings: Settings,
    cost_tracker: CostTracker,
    asset_cache: AssetCache,
) -> OrchestratorAgent:
    """Wireia todos os agentes com seus providers concretos."""
    llm = AnthropicLLMProvider(api_key=settings.anthropic_api_key)
    image = GeminiImageProvider(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model_image,
    )
    storage = SupabaseStorage(build_supabase_admin_client(settings))

    content = ContentAgent(
        llm=llm,
        cost_tracker=cost_tracker,
        model=settings.anthropic_model_content,
    )
    visual = VisualAgent(
        image_provider=image,
        cost_tracker=cost_tracker,
        asset_cache=asset_cache,
        storage=storage,
        model=settings.gemini_model_image,
    )
    brand = BrandAgent(
        llm=llm,
        cost_tracker=cost_tracker,
        model=settings.anthropic_model_brand,
    )

    return OrchestratorAgent(
        llm=llm,
        content=content,
        visual=visual,
        brand=brand,
        cost_tracker=cost_tracker,
        model=settings.anthropic_model_orchestrator,
    )


__all__ = [
    "BrandAgent",
    "ContentAgent",
    "OrchestratorAgent",
    "VisualAgent",
    "build_orchestrator",
]

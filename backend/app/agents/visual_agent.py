import hashlib
import json
from typing import Any
from uuid import UUID

from app.agents.protocols import AssetCache, CostTracker
from app.integrations.image_provider import ImageProvider
from app.integrations.supabase_client import SupabaseStorage
from app.models.brand_memory import BrandMemory
from app.models.template import Template


class VisualAgent:
    """
    Não chama LLM — chama um ImageProvider (Gemini Flash Image).
    Sempre verifica cache em mkt_assets.metadata->>'cache_hash' antes de gerar.
    """

    BUCKET = "mkt-generations"

    def __init__(
        self,
        *,
        image_provider: ImageProvider,
        cost_tracker: CostTracker,
        asset_cache: AssetCache,
        storage: SupabaseStorage,
        model: str,
    ) -> None:
        self._image = image_provider
        self._cost_tracker = cost_tracker
        self._asset_cache = asset_cache
        self._storage = storage
        self._model = model

    async def generate(
        self,
        *,
        visual_brief: str,
        brand: BrandMemory,
        template: Template,
        generation_id: UUID,
        tenant_id: UUID,
    ) -> dict[str, Any]:
        cache_hash = self._compute_cache_hash(visual_brief, brand, template)

        cached_path = await self._asset_cache.lookup(
            cache_hash=cache_hash, tenant_id=tenant_id
        )
        if cached_path:
            return {
                "storage_path": cached_path,
                "cache_hit": True,
                "cache_hash": cache_hash,
            }

        prompt = self._build_prompt(visual_brief, brand)
        result = await self._image.generate(
            prompt=prompt,
            width=template.dimensions.width,
            height=template.dimensions.height,
        )

        path = f"{tenant_id}/{generation_id}/background.png"
        self._storage.upload(
            bucket=self.BUCKET,
            path=path,
            data=result.png_bytes,
            content_type="image/png",
        )

        await self._cost_tracker.track(
            generation_id=generation_id,
            agent_name="visual",
            model=result.model,
            input={
                "visual_brief": visual_brief,
                "template_id": str(template.id),
                "width": template.dimensions.width,
                "height": template.dimensions.height,
            },
            output={"storage_path": path, "cache_hash": cache_hash},
            tokens_in=0,
            tokens_out=0,
            latency_ms=result.latency_ms,
        )

        await self._asset_cache.save(
            generation_id=generation_id,
            cache_hash=cache_hash,
            storage_path=path,
            metadata={
                "cache_hash": cache_hash,
                "model": result.model,
                "width": template.dimensions.width,
                "height": template.dimensions.height,
                **result.metadata,
            },
        )

        return {
            "storage_path": path,
            "cache_hit": False,
            "cache_hash": cache_hash,
        }

    @staticmethod
    def _compute_cache_hash(
        visual_brief: str, brand: BrandMemory, template: Template
    ) -> str:
        identity_json = json.dumps(
            brand.visual_identity.model_dump(), sort_keys=True, ensure_ascii=False
        )
        payload = visual_brief + identity_json + str(template.id)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_prompt(visual_brief: str, brand: BrandMemory) -> str:
        vi = brand.visual_identity
        parts = [visual_brief]
        if vi.style_description:
            parts.append(f"Style: {vi.style_description}")
        colors = [c for c in (vi.primary_color, vi.secondary_color) if c]
        if colors:
            parts.append("Color palette: " + ", ".join(colors))
        return "\n\n".join(parts)

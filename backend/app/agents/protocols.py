"""
Interfaces que os agentes consomem. Implementações concretas em services/.
Mantém os agentes desacoplados de detalhes de persistência.
"""
from typing import Any, Protocol
from uuid import UUID


class CostTracker(Protocol):
    async def track(
        self,
        *,
        generation_id: UUID,
        agent_name: str,
        model: str,
        input: dict[str, Any],
        output: dict[str, Any],
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
    ) -> int:
        """Persiste linha em mkt_agent_logs e devolve cost_cents calculado."""
        ...


class AssetCache(Protocol):
    async def lookup(
        self,
        *,
        cache_hash: str,
        tenant_id: UUID,
    ) -> str | None:
        """Hit → storage_path; miss → None."""
        ...

    async def save(
        self,
        *,
        generation_id: UUID,
        cache_hash: str,
        storage_path: str,
        metadata: dict[str, Any],
    ) -> None:
        """Cria mkt_assets com type=image_png e metadata.cache_hash."""
        ...

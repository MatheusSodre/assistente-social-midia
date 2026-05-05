from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ImageResult:
    png_bytes: bytes
    model: str
    latency_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)


class ImageProvider(Protocol):
    async def generate(
        self,
        *,
        prompt: str,
        width: int,
        height: int,
        seed: int | None = None,
    ) -> ImageResult:
        ...

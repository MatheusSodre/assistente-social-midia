from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMResponse:
    text: str | None
    tool_use: dict[str, Any] | None
    tokens_in: int
    tokens_out: int
    model: str
    latency_ms: int


class LLMProvider(Protocol):
    async def complete(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        ...

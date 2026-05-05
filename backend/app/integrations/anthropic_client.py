import time
from typing import Any

from anthropic import AsyncAnthropic

from app.integrations.llm_provider import LLMResponse


class AnthropicLLMProvider:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key)

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
        start = time.monotonic()

        kwargs: dict[str, Any] = {
            "model": model,
            "system": system,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        response = await self._client.messages.create(**kwargs)

        latency_ms = int((time.monotonic() - start) * 1000)

        text_parts: list[str] = []
        tool_use: dict[str, Any] | None = None
        for block in response.content:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_parts.append(block.text)
            elif block_type == "tool_use":
                tool_use = {"name": block.name, "input": block.input, "id": block.id}

        return LLMResponse(
            text="\n".join(text_parts) if text_parts else None,
            tool_use=tool_use,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            model=response.model,
            latency_ms=latency_ms,
        )

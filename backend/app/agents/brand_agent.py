import json
from pathlib import Path
from typing import Any
from uuid import UUID

from app.agents.protocols import CostTracker
from app.integrations.llm_provider import LLMProvider
from app.models.brand_memory import BrandMemory


_PROMPT_PATH = Path(__file__).parent / "prompts" / "brand.md"


BRAND_TOOL: dict[str, Any] = {
    "name": "submit_brand_review",
    "description": "Submete o resultado da revisão de aderência à marca.",
    "input_schema": {
        "type": "object",
        "required": ["approved", "reason"],
        "properties": {
            "approved": {"type": "boolean"},
            "reason": {
                "type": "string",
                "maxLength": 200,
                "description": "Justificativa curta da decisão.",
            },
            "suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
                "description": "Sugestões acionáveis. Vazio se totalmente aprovado.",
            },
        },
    },
}


class BrandAgent:
    def __init__(
        self,
        *,
        llm: LLMProvider,
        cost_tracker: CostTracker,
        model: str,
    ) -> None:
        self._llm = llm
        self._cost_tracker = cost_tracker
        self._model = model
        self._system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    async def review(
        self,
        *,
        content: dict[str, Any],
        brand: BrandMemory,
        generation_id: UUID,
    ) -> dict[str, Any]:
        user_message = (
            "# Conteúdo gerado\n```json\n"
            f"{json.dumps(content, ensure_ascii=False, indent=2)}\n```\n\n"
            "# Brand Memory\n```json\n"
            f"{brand.model_dump_json(indent=2)}\n```"
        )

        response = await self._llm.complete(
            model=self._model,
            system=self._system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=[BRAND_TOOL],
            tool_choice={"type": "tool", "name": "submit_brand_review"},
            max_tokens=600,
        )

        if not response.tool_use:
            raise RuntimeError(
                f"BrandAgent: tool_use ausente na resposta. text={response.text!r}"
            )

        review = response.tool_use["input"]
        review.setdefault("suggestions", [])

        await self._cost_tracker.track(
            generation_id=generation_id,
            agent_name="brand",
            model=response.model,
            input={"content": content},
            output=review,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            latency_ms=response.latency_ms,
        )

        return review

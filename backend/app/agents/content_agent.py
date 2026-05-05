from pathlib import Path
from typing import Any
from uuid import UUID

from app.agents.protocols import CostTracker
from app.integrations.llm_provider import LLMProvider
from app.models.brand_memory import BrandMemory


_PROMPT_PATH = Path(__file__).parent / "prompts" / "content.md"


CONTENT_TOOL: dict[str, Any] = {
    "name": "submit_post_content",
    "description": "Submete o conteúdo finalizado do post de Instagram.",
    "input_schema": {
        "type": "object",
        "required": ["caption", "hashtags", "visual_brief", "headline"],
        "properties": {
            "caption": {
                "type": "string",
                "maxLength": 2200,
                "description": "Texto completo da legenda do post em PT-BR.",
            },
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 8,
                "maxItems": 30,
                "description": "Hashtags relevantes (com '#').",
            },
            "visual_brief": {
                "type": "string",
                "description": "Descrição em prosa do que a imagem deve mostrar (sem texto sobreposto).",
            },
            "headline": {
                "type": "string",
                "maxLength": 80,
                "description": "Texto curto que vai sobre a imagem (composto via Konva).",
            },
        },
    },
}


class ContentAgent:
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

    async def generate(
        self,
        *,
        brief: str,
        plan: str,
        brand: BrandMemory,
        generation_id: UUID,
    ) -> dict[str, Any]:
        user_message = self._build_user_message(brief, plan, brand)

        response = await self._llm.complete(
            model=self._model,
            system=self._system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=[CONTENT_TOOL],
            tool_choice={"type": "tool", "name": "submit_post_content"},
            max_tokens=2000,
        )

        if not response.tool_use:
            raise RuntimeError(
                f"ContentAgent: tool_use ausente na resposta. text={response.text!r}"
            )

        await self._cost_tracker.track(
            generation_id=generation_id,
            agent_name="content",
            model=response.model,
            input={"brief": brief, "plan": plan},
            output=response.tool_use["input"],
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            latency_ms=response.latency_ms,
        )

        return response.tool_use["input"]

    @staticmethod
    def _build_user_message(brief: str, plan: str, brand: BrandMemory) -> str:
        return (
            f"# Briefing\n{brief}\n\n"
            f"# Plano de conteúdo (do Orchestrator)\n{plan}\n\n"
            f"# Brand Memory\n```json\n{brand.model_dump_json(indent=2)}\n```"
        )

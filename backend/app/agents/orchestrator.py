from pathlib import Path
from typing import Awaitable, Callable
from uuid import UUID

from app.agents.brand_agent import BrandAgent
from app.agents.content_agent import ContentAgent
from app.agents.protocols import CostTracker
from app.agents.visual_agent import VisualAgent
from app.integrations.llm_provider import LLMProvider
from app.models.brand_memory import BrandMemory
from app.models.generation import GenerationResult, GenerationStatus
from app.models.template import Template


_PROMPT_PATH = Path(__file__).parent / "prompts" / "orchestrator.md"

StatusSetter = Callable[[GenerationStatus], Awaitable[None]]


class OrchestratorAgent:
    """
    Recebe briefing + Brand Memory + Template, gera plano via LLM,
    delega Content → Visual → Brand em sequência.
    Faz no máximo 1 retry se BrandAgent reprovar.
    """

    MAX_RETRY_ON_REJECT = 1

    def __init__(
        self,
        *,
        llm: LLMProvider,
        content: ContentAgent,
        visual: VisualAgent,
        brand: BrandAgent,
        cost_tracker: CostTracker,
        model: str,
    ) -> None:
        self._llm = llm
        self._content = content
        self._visual = visual
        self._brand = brand
        self._cost_tracker = cost_tracker
        self._model = model
        self._system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    async def run(
        self,
        *,
        brief: str,
        brand: BrandMemory,
        template: Template,
        generation_id: UUID,
        tenant_id: UUID,
        set_status: StatusSetter,
    ) -> GenerationResult:
        await set_status(GenerationStatus.BRAND_LOADING)
        plan = await self._generate_plan(brief, brand, generation_id)

        last_content: dict | None = None
        last_visual: dict | None = None
        last_review: dict | None = None

        for attempt in range(self.MAX_RETRY_ON_REJECT + 1):
            await set_status(GenerationStatus.CONTENT_GENERATING)
            last_content = await self._content.generate(
                brief=brief,
                plan=plan,
                brand=brand,
                generation_id=generation_id,
            )

            await set_status(GenerationStatus.IMAGE_GENERATING)
            last_visual = await self._visual.generate(
                visual_brief=last_content["visual_brief"],
                brand=brand,
                template=template,
                generation_id=generation_id,
                tenant_id=tenant_id,
            )

            await set_status(GenerationStatus.VALIDATING)
            last_review = await self._brand.review(
                content=last_content,
                brand=brand,
                generation_id=generation_id,
            )

            if last_review["approved"]:
                break

        assert last_content and last_visual and last_review

        return GenerationResult(
            caption=last_content["caption"],
            hashtags=last_content["hashtags"],
            headline=last_content["headline"],
            visual_brief=last_content["visual_brief"],
            background_path=last_visual["storage_path"],
            brand_review=last_review,
        )

    async def _generate_plan(
        self, brief: str, brand: BrandMemory, generation_id: UUID
    ) -> str:
        user_message = (
            f"# Briefing\n{brief}\n\n"
            f"# Brand Memory\n```json\n{brand.model_dump_json(indent=2)}\n```"
        )
        response = await self._llm.complete(
            model=self._model,
            system=self._system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=300,
        )

        plan = (response.text or "").strip()
        if not plan:
            raise RuntimeError("OrchestratorAgent: plano vazio retornado pelo LLM")

        await self._cost_tracker.track(
            generation_id=generation_id,
            agent_name="orchestrator",
            model=response.model,
            input={"brief": brief},
            output={"plan": plan},
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            latency_ms=response.latency_ms,
        )
        return plan

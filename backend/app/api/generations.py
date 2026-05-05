import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_generation_service
from app.core.auth import CurrentUser, get_current_user
from app.core.db import listen_notify
from app.models.generation import Generation, GenerationCreate, GenerationStatus
from app.services.generation_service import GenerationService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/generations", tags=["generations"])

_TERMINAL_STATUSES = {GenerationStatus.DONE.value, GenerationStatus.FAILED.value}


@router.post("", response_model=Generation, status_code=status.HTTP_201_CREATED)
async def create_generation(
    payload: GenerationCreate,
    background: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    service: GenerationService = Depends(get_generation_service),
):
    generation_id = await service.create(
        tenant_id=user.tenant_id,
        created_by=user.user_id,
        brief=payload.brief,
        template_id=payload.template_id,
    )
    background.add_task(
        service.run_pipeline,
        generation_id=generation_id,
        tenant_id=user.tenant_id,
    )
    generation = await service.get(
        tenant_id=user.tenant_id, generation_id=generation_id
    )
    if not generation:
        raise HTTPException(status_code=500, detail="Generation desapareceu após insert")
    return generation


@router.get("", response_model=list[Generation])
async def list_generations(
    limit: int = 50,
    user: CurrentUser = Depends(get_current_user),
    service: GenerationService = Depends(get_generation_service),
):
    return await service.list_all(tenant_id=user.tenant_id, limit=limit)


@router.get("/{generation_id}", response_model=Generation)
async def get_generation(
    generation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: GenerationService = Depends(get_generation_service),
):
    generation = await service.get(
        tenant_id=user.tenant_id, generation_id=generation_id
    )
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation


@router.get("/{generation_id}/stream")
async def stream_generation(
    generation_id: UUID,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    service: GenerationService = Depends(get_generation_service),
):
    """SSE: empurra evento a cada NOTIFY no canal generation_<id>."""
    pool = request.app.state.pool
    channel = f"generation_{generation_id}"

    initial = await service.get(
        tenant_id=user.tenant_id, generation_id=generation_id
    )
    if not initial:
        raise HTTPException(status_code=404, detail="Generation not found")

    async def event_generator():
        # estado atual primeiro
        yield {
            "event": "status",
            "data": json.dumps({"status": initial.status.value}),
        }
        if initial.status.value in _TERMINAL_STATUSES:
            return

        queue: asyncio.Queue[str] = asyncio.Queue()

        def listener(connection, pid, ch, payload):
            queue.put_nowait(payload)

        async with listen_notify(pool, channel) as conn:
            await conn.add_listener(channel, listener)
            try:
                while True:
                    if await request.is_disconnected():
                        return

                    try:
                        payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    except asyncio.TimeoutError:
                        # heartbeat pra manter conexão viva
                        yield {"event": "ping", "data": ""}
                        continue

                    yield {"event": "status", "data": payload}

                    try:
                        parsed = json.loads(payload)
                    except json.JSONDecodeError:
                        parsed = {}
                    if parsed.get("status") in _TERMINAL_STATUSES:
                        return
            finally:
                await conn.remove_listener(channel, listener)

    return EventSourceResponse(event_generator())

"""
Endpoints CRUD pra conversas e mensagens da Lia.
O endpoint de chat (POST /chat com SSE) vem no PROMPT 04.5 — esse arquivo só lê/escreve.
"""
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_lia_service
from app.core.auth import CurrentUser, get_current_user
from app.models.lia import LiaConversation, LiaMessage
from app.services.lia_service import LiaService


router = APIRouter(prefix="/api/v1/lia", tags=["lia"])


@router.get("/conversations", response_model=list[LiaConversation])
async def list_conversations(
    user: CurrentUser = Depends(get_current_user),
    service: LiaService = Depends(get_lia_service),
):
    return await service.list_conversations(tenant_id=user.tenant_id)


@router.post("/conversations", response_model=LiaConversation)
async def create_or_get_active(
    user: CurrentUser = Depends(get_current_user),
    service: LiaService = Depends(get_lia_service),
):
    return await service.get_or_create_active(
        tenant_id=user.tenant_id, user_id=user.user_id
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[LiaMessage])
async def list_messages(
    conversation_id: UUID,
    limit: int = 100,
    user: CurrentUser = Depends(get_current_user),
    service: LiaService = Depends(get_lia_service),
):
    return await service.list_messages(
        tenant_id=user.tenant_id,
        conversation_id=conversation_id,
        limit=limit,
    )


@router.post("/conversations/{conversation_id}/close", status_code=204)
async def close_conversation(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: LiaService = Depends(get_lia_service),
):
    await service.close_conversation(
        tenant_id=user.tenant_id, conversation_id=conversation_id
    )

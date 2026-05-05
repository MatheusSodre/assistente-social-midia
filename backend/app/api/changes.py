from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import get_change_service
from app.core.auth import CurrentUser, get_current_user
from app.models.pending_change import (
    PendingChange,
    PendingChangeCreate,
)
from app.services.change_service import ChangeService


router = APIRouter(prefix="/api/v1/changes", tags=["changes"])


@router.get("", response_model=list[PendingChange])
async def list_pending(
    user: CurrentUser = Depends(get_current_user),
    service: ChangeService = Depends(get_change_service),
):
    return await service.list_pending(tenant_id=user.tenant_id)


@router.post("", response_model=PendingChange, status_code=status.HTTP_201_CREATED)
async def create_pending_change(
    payload: PendingChangeCreate,
    user: CurrentUser = Depends(get_current_user),
    service: ChangeService = Depends(get_change_service),
):
    return await service.propose(
        tenant_id=user.tenant_id,
        proposed_by_user_id=user.user_id,
        payload=payload,
    )


@router.get("/{change_id}", response_model=PendingChange)
async def get_change(
    change_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: ChangeService = Depends(get_change_service),
):
    return await service.get(tenant_id=user.tenant_id, change_id=change_id)


@router.post("/{change_id}/accept", response_model=PendingChange)
async def accept_change(
    change_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: ChangeService = Depends(get_change_service),
):
    return await service.accept(
        tenant_id=user.tenant_id,
        change_id=change_id,
        resolved_by_user_id=user.user_id,
    )


@router.post("/{change_id}/reject", response_model=PendingChange)
async def reject_change(
    change_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: ChangeService = Depends(get_change_service),
):
    return await service.reject(
        tenant_id=user.tenant_id,
        change_id=change_id,
        resolved_by_user_id=user.user_id,
    )

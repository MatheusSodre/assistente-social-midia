from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_source_service
from app.core.auth import CurrentUser, get_current_user
from app.models.source import Source, SourceCreate
from app.services.source_service import SourceService


router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("", response_model=list[Source])
async def list_sources(
    user: CurrentUser = Depends(get_current_user),
    service: SourceService = Depends(get_source_service),
):
    return await service.list_all(tenant_id=user.tenant_id)


@router.post("", response_model=Source, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    user: CurrentUser = Depends(get_current_user),
    service: SourceService = Depends(get_source_service),
):
    return await service.create(
        tenant_id=user.tenant_id,
        added_by_user_id=user.user_id,
        payload=payload,
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: SourceService = Depends(get_source_service),
):
    deleted = await service.delete(tenant_id=user.tenant_id, source_id=source_id)
    if not deleted:
        raise HTTPException(404, "source not found")


@router.post("/{source_id}/reindex", response_model=Source)
async def reindex_source(
    source_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: SourceService = Depends(get_source_service),
):
    src = await service.reindex(tenant_id=user.tenant_id, source_id=source_id)
    if not src:
        raise HTTPException(404, "source not found")
    return src

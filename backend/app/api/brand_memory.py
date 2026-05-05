from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_brand_service
from app.core.auth import CurrentUser, get_current_user
from app.models.brand_memory import (
    BrandMemory,
    BrandMemoryCreate,
    BrandMemoryUpdate,
)
from app.services.brand_memory_service import BrandMemoryService


router = APIRouter(prefix="/api/v1/brand-memory", tags=["brand-memory"])


@router.get("", response_model=list[BrandMemory])
async def list_brand_memories(
    user: CurrentUser = Depends(get_current_user),
    service: BrandMemoryService = Depends(get_brand_service),
):
    return await service.list_all(tenant_id=user.tenant_id)


@router.post("", response_model=BrandMemory, status_code=status.HTTP_201_CREATED)
async def create_brand_memory(
    payload: BrandMemoryCreate,
    user: CurrentUser = Depends(get_current_user),
    service: BrandMemoryService = Depends(get_brand_service),
):
    return await service.create(tenant_id=user.tenant_id, payload=payload)


@router.get("/{brand_id}", response_model=BrandMemory)
async def get_brand_memory(
    brand_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: BrandMemoryService = Depends(get_brand_service),
):
    brand = await service.get(tenant_id=user.tenant_id, brand_id=brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand memory not found")
    return brand


@router.patch("/{brand_id}", response_model=BrandMemory)
async def update_brand_memory(
    brand_id: UUID,
    payload: BrandMemoryUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: BrandMemoryService = Depends(get_brand_service),
):
    brand = await service.update(
        tenant_id=user.tenant_id, brand_id=brand_id, payload=payload
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand memory not found")
    return brand


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand_memory(
    brand_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: BrandMemoryService = Depends(get_brand_service),
):
    deleted = await service.delete(tenant_id=user.tenant_id, brand_id=brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Brand memory not found")

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_brand_block_service
from app.core.auth import CurrentUser, get_current_user
from app.models.brand_block import (
    BlockKey,
    BrandBlock,
    BrandBlockVersion,
    BrandMemoryDashboard,
)
from app.services.brand_block_service import BrandBlockService


router = APIRouter(prefix="/api/v1/brand-memory", tags=["brand-memory"])


@router.get("", response_model=BrandMemoryDashboard)
async def get_brand_memory(
    user: CurrentUser = Depends(get_current_user),
    service: BrandBlockService = Depends(get_brand_block_service),
):
    return await service.get_dashboard(tenant_id=user.tenant_id)


@router.get("/blocks/{block_key}", response_model=BrandBlock)
async def get_block(
    block_key: BlockKey,
    user: CurrentUser = Depends(get_current_user),
    service: BrandBlockService = Depends(get_brand_block_service),
):
    block = await service.get_block(tenant_id=user.tenant_id, block_key=block_key)
    if not block:
        raise HTTPException(404, "block not found")
    return block


@router.get(
    "/blocks/{block_key}/versions",
    response_model=list[BrandBlockVersion],
)
async def list_versions(
    block_key: BlockKey,
    limit: int = 50,
    user: CurrentUser = Depends(get_current_user),
    service: BrandBlockService = Depends(get_brand_block_service),
):
    return await service.list_versions(
        tenant_id=user.tenant_id, block_key=block_key, limit=limit
    )


@router.post("/blocks/{block_key}/revert/{version_number}", response_model=BrandBlock)
async def revert_to_version(
    block_key: BlockKey,
    version_number: int,
    user: CurrentUser = Depends(get_current_user),
    service: BrandBlockService = Depends(get_brand_block_service),
):
    return await service.revert_to_version(
        tenant_id=user.tenant_id,
        block_key=block_key,
        version_number=version_number,
    )

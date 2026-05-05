from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_generation_service, get_storage_service
from app.core.auth import CurrentUser, get_current_user
from app.models.asset import AssetType
from app.services.generation_service import GenerationService
from app.services.storage_service import StorageService


router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("/{generation_id}/{asset_type}")
async def get_asset_signed_url(
    generation_id: UUID,
    asset_type: AssetType,
    user: CurrentUser = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    generation_service: GenerationService = Depends(get_generation_service),
):
    generation = await generation_service.get(
        tenant_id=user.tenant_id, generation_id=generation_id
    )
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    if asset_type == AssetType.IMAGE_PNG:
        bucket = StorageService.BUCKET_GENERATIONS
        path = StorageService.background_path(user.tenant_id, generation_id)
    elif asset_type == AssetType.CAROUSEL_ZIP:
        bucket = StorageService.BUCKET_EXPORTS
        path = StorageService.carousel_zip_path(user.tenant_id, generation_id)
    elif asset_type == AssetType.COPY_TEXT:
        bucket = StorageService.BUCKET_EXPORTS
        path = StorageService.copy_text_path(user.tenant_id, generation_id)
    else:
        raise HTTPException(status_code=400, detail="Unknown asset type")

    url = storage.signed_url(bucket=bucket, path=path, ttl_seconds=300)
    return {"url": url, "expires_in": 300}

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_template_service
from app.core.auth import CurrentUser, get_current_user
from app.models.template import Template
from app.services.template_service import TemplateService


router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


@router.get("", response_model=list[Template])
async def list_templates(
    user: CurrentUser = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
):
    return await service.list_all(tenant_id=user.tenant_id)


@router.get("/{template_id}", response_model=Template)
async def get_template(
    template_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
):
    tpl = await service.get(tenant_id=user.tenant_id, template_id=template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.designer.pixel_agent import run_pixel, _get_identity, _save_identity
from .schemas import DesignerChatResponse, VisualIdentity

router = APIRouter(prefix="/api/v1/designer", tags=["designer"])
logger = logging.getLogger(__name__)


def _verify_business(business_id: str, user_sub: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, user_sub),
            )
            b = cur.fetchone()
    if not b:
        raise HTTPException(404, "Business não encontrado")


@router.post("/chat", response_model=DesignerChatResponse)
async def designer_chat(
    business_id: str = Form(...),
    message: str = Form(""),
    image: Optional[UploadFile] = File(None),
    user=Depends(get_current_user),
):
    _verify_business(business_id, user["sub"])

    image_bytes: bytes | None = None
    if image and image.filename:
        image_bytes = await image.read()

    result = await run_pixel(
        business_id=business_id,
        usuario_id=user["sub"],
        user_message=message,
        image_bytes=image_bytes,
    )
    return DesignerChatResponse(**result)


@router.get("/identity/{business_id}")
def get_identity(business_id: str, user=Depends(get_current_user)):
    _verify_business(business_id, user["sub"])
    return _get_identity(business_id)


@router.put("/identity/{business_id}")
def update_identity(business_id: str, data: VisualIdentity, user=Depends(get_current_user)):
    _verify_business(business_id, user["sub"])
    result = _save_identity(business_id, data.model_dump(exclude_none=True))
    return result


@router.delete("/history/{business_id}")
def clear_history(business_id: str, user=Depends(get_current_user)):
    _verify_business(business_id, user["sub"])
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM designer_conversations WHERE business_id = %s", (business_id,))
    return {"message": "Histórico limpo"}

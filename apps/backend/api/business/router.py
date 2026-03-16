import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.publisher.token_manager import encrypt_token, decrypt_token
from .schemas import BusinessCreate, BusinessUpdate, InstagramConnect

router = APIRouter(prefix="/api/v1/businesses", tags=["businesses"])


@router.post("")
def create_business(data: BusinessCreate, user=Depends(get_current_user)) -> dict[str, Any]:
    bid = str(uuid.uuid4())
    now = datetime.utcnow()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO businesses (id, usuario_id, name, type, brand_context, criado_em, atualizado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (bid, user["sub"], data.name, data.type,
                 json.dumps(data.brand_context) if data.brand_context else None, now, now),
            )
    return {"id": bid, "name": data.name, "type": data.type}


@router.get("")
def list_businesses(user=Depends(get_current_user)) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, type, instagram_account_id, brand_context, criado_em FROM businesses WHERE usuario_id = %s",
                (user["sub"],),
            )
            rows = cur.fetchall()
    return rows or []


@router.get("/{business_id}")
def get_business(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, type, instagram_account_id, brand_context, criado_em FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, user["sub"]),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Business não encontrado")
    return row


@router.post("/{business_id}/connect-instagram")
def connect_instagram(business_id: str, data: InstagramConnect, user=Depends(get_current_user)) -> dict[str, Any]:
    # Verifica ownership
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, user["sub"]),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Business não encontrado")
            encrypted = encrypt_token(data.access_token)
            cur.execute(
                "UPDATE businesses SET instagram_account_id = %s, instagram_access_token = %s, atualizado_em = NOW() WHERE id = %s",
                (data.instagram_account_id, encrypted, business_id),
            )
    return {"message": "Instagram conectado com sucesso", "instagram_account_id": data.instagram_account_id}

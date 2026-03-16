import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.ads_agent.luna_agent import run_luna
from .schemas import AdsAccountConnect, LunaChatRequest

router = APIRouter(prefix="/api/v1/ads", tags=["ads"])


def _verify_business(business_id: str, usuario_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, usuario_id),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Business não encontrado")


@router.get("/account/{business_id}")
def get_account(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_business(business_id, user["sub"])
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, customer_id, login_customer_id, is_test_account, criado_em FROM google_ads_accounts WHERE business_id = %s",
                (business_id,),
            )
            row = cur.fetchone()
    if not row:
        return {"connected": False, "business_id": business_id}
    return {"connected": True, **row}


@router.post("/account/connect")
def connect_account(data: AdsAccountConnect, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_business(data.business_id, user["sub"])

    # Encrypt refresh_token
    try:
        from src.engines.ads.google_ads_client import _encrypt_token
        encrypted_token = _encrypt_token(data.refresh_token)
    except Exception:
        encrypted_token = data.refresh_token

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM google_ads_accounts WHERE business_id = %s",
                (data.business_id,),
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    """UPDATE google_ads_accounts
                       SET customer_id = %s, login_customer_id = %s, refresh_token = %s,
                           is_test_account = %s, atualizado_em = NOW()
                       WHERE business_id = %s""",
                    (data.customer_id, data.login_customer_id, encrypted_token,
                     int(data.is_test_account), data.business_id),
                )
            else:
                cur.execute(
                    """INSERT INTO google_ads_accounts
                       (id, business_id, customer_id, login_customer_id, refresh_token, is_test_account)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (str(uuid.uuid4()), data.business_id, data.customer_id,
                     data.login_customer_id, encrypted_token, int(data.is_test_account)),
                )

    return {"message": "Conta Google Ads conectada!", "customer_id": data.customer_id}


@router.delete("/account/{business_id}")
def disconnect_account(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_business(business_id, user["sub"])
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM google_ads_accounts WHERE business_id = %s", (business_id,))
    return {"message": "Conta Google Ads desconectada"}


@router.post("/chat")
async def luna_chat(data: LunaChatRequest, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_business(data.business_id, user["sub"])
    result = await run_luna(
        business_id=data.business_id,
        usuario_id=user["sub"],
        user_message=data.message,
    )
    return result


@router.get("/history/{business_id}")
def get_history(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_business(business_id, user["sub"])
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT messages FROM luna_conversations WHERE business_id = %s",
                (business_id,),
            )
            row = cur.fetchone()

    if not row:
        return {"messages": [], "business_id": business_id}

    msgs = row["messages"]
    if isinstance(msgs, str):
        msgs = json.loads(msgs)

    clean = []
    for m in (msgs or []):
        role = m.get("role")
        content = m.get("content")
        if role == "user" and isinstance(content, str):
            clean.append({"role": "user", "content": content})
        elif role == "assistant" and isinstance(content, list):
            text = next((b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"), None)
            if text:
                clean.append({"role": "assistant", "content": text})
    return {"messages": clean, "business_id": business_id}


@router.delete("/history/{business_id}")
def clear_history(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_business(business_id, user["sub"])
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM luna_conversations WHERE business_id = %s", (business_id,))
    return {"message": "Histórico da Luna limpo"}

"""
Billing & Subscription API — gerencia planos, limites e uso.
"""
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from .schemas import PLAN_LIMITS

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


def _ensure_subscription(usuario_id: str) -> dict:
    """Garante que o usuário tem uma subscription. Cria trial se não existir."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM subscriptions WHERE usuario_id = %s", (usuario_id,))
            sub = cur.fetchone()
            if sub:
                return sub

            # Criar trial de 7 dias
            sub_id = str(uuid.uuid4())
            now = datetime.utcnow()
            trial_end = now + timedelta(days=7)
            cur.execute(
                """INSERT INTO subscriptions
                   (id, usuario_id, plano, status, trial_ends_at, posts_used_this_month, posts_reset_at)
                   VALUES (%s, %s, 'pro', 'trial', %s, 0, %s)""",
                (sub_id, usuario_id, trial_end, now + timedelta(days=30)),
            )
            cur.execute("SELECT * FROM subscriptions WHERE id = %s", (sub_id,))
            return cur.fetchone()


def get_subscription_info(usuario_id: str) -> dict[str, Any]:
    """Retorna info da subscription com limites calculados."""
    sub = _ensure_subscription(usuario_id)
    plano = sub["plano"]
    limits = PLAN_LIMITS.get(plano, PLAN_LIMITS["starter"])

    # Reset mensal do contador se necessário
    now = datetime.utcnow()
    reset_at = sub.get("posts_reset_at")
    posts_used = sub.get("posts_used_this_month", 0)
    if reset_at and now >= reset_at:
        posts_used = 0
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE subscriptions SET posts_used_this_month = 0, posts_reset_at = %s WHERE usuario_id = %s",
                    (now + timedelta(days=30), usuario_id),
                )

    return {
        "plano": plano,
        "status": sub["status"],
        "posts_used": posts_used,
        "posts_limit": limits["posts_per_month"],
        "businesses_limit": limits["businesses"],
        "instagram_limit": limits["instagram_accounts"],
        "formats": limits["formats"],
        "agents": limits["agents"],
        "ig_style_analysis": limits["ig_style_analysis"],
        "trial_ends_at": str(sub.get("trial_ends_at", "")) if sub.get("trial_ends_at") else None,
        "current_period_end": str(sub.get("current_period_end", "")) if sub.get("current_period_end") else None,
    }


def increment_post_count(usuario_id: str) -> None:
    """Incrementa o contador de posts usados no mês."""
    _ensure_subscription(usuario_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE subscriptions SET posts_used_this_month = posts_used_this_month + 1 WHERE usuario_id = %s",
                (usuario_id,),
            )


def check_can_generate(usuario_id: str, format: str = "post") -> dict[str, Any]:
    """Verifica se o usuário pode gerar conteúdo. Retorna erro se não puder."""
    info = get_subscription_info(usuario_id)

    # Verificar status
    if info["status"] == "expired":
        return {"allowed": False, "reason": "Sua assinatura expirou. Renove para continuar criando conteudo."}
    if info["status"] == "cancelled":
        return {"allowed": False, "reason": "Assinatura cancelada. Reative para continuar."}

    # Verificar trial expirado
    if info["status"] == "trial" and info.get("trial_ends_at"):
        from datetime import datetime
        try:
            trial_end = datetime.fromisoformat(info["trial_ends_at"].replace(" ", "T").split(".")[0])
            if datetime.utcnow() > trial_end:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE subscriptions SET status = 'expired' WHERE usuario_id = %s",
                            (usuario_id,),
                        )
                return {"allowed": False, "reason": "Seu trial de 7 dias expirou. Escolha um plano para continuar."}
        except Exception:
            pass

    # Verificar limite de posts
    if info["posts_used"] >= info["posts_limit"]:
        return {"allowed": False, "reason": f"Limite de {info['posts_limit']} posts/mes atingido. Faca upgrade para continuar."}

    # Verificar formato permitido
    if format not in info["formats"]:
        return {"allowed": False, "reason": f"O formato '{format}' nao esta disponivel no plano {info['plano']}. Faca upgrade."}

    return {"allowed": True}


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/subscription")
def get_subscription(user=Depends(get_current_user)) -> dict[str, Any]:
    """Retorna a subscription atual do usuário com limites e uso."""
    return get_subscription_info(user["sub"])


@router.post("/upgrade")
def upgrade_plan(plano: str, user=Depends(get_current_user)) -> dict[str, Any]:
    """Upgrade de plano (placeholder — integração Stripe futura)."""
    if plano not in PLAN_LIMITS:
        raise HTTPException(400, f"Plano invalido: {plano}")

    _ensure_subscription(user["sub"])
    now = datetime.utcnow()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE subscriptions
                   SET plano = %s, status = 'active',
                       current_period_start = %s, current_period_end = %s,
                       atualizado_em = NOW()
                   WHERE usuario_id = %s""",
                (plano, now, now + timedelta(days=30), user["sub"]),
            )

    return {"message": f"Plano atualizado para {plano}", "plano": plano}

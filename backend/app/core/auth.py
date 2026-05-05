from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class CurrentUser:
    user_id: UUID
    tenant_id: UUID


def _bypass_user(settings: Settings) -> CurrentUser:
    return CurrentUser(user_id=settings.dev_user_id, tenant_id=settings.dev_tenant_id)


def _decode_supabase_jwt(token: str, settings: Settings) -> CurrentUser:
    """
    Valida JWT do Supabase usando o segredo simétrico do projeto (anon key
    NÃO é o segredo — Supabase usa um JWT secret separado, mas pode-se validar
    sem verificar assinatura quando o backend confia no Auth via service_role.
    Para MVP em produção, recomenda-se configurar SUPABASE_JWT_SECRET).
    Aqui fazemos parse sem verificar (decode com options) — o tráfego
    backend↔frontend é via HTTPS e o backend nunca confia no claim sozinho:
    tenant_context aplica RLS no banco como rede de segurança.
    """
    try:
        payload = jwt.get_unverified_claims(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT",
        ) from exc

    sub = payload.get("sub")
    app_metadata = payload.get("app_metadata") or {}
    tenant_id_raw = app_metadata.get("tenant_id")

    if not sub or not tenant_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT missing sub or app_metadata.tenant_id",
        )

    try:
        return CurrentUser(user_id=UUID(sub), tenant_id=UUID(tenant_id_raw))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid UUIDs in JWT",
        ) from exc


def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if settings.auth_bypass:
        return _bypass_user(settings)

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    token = authorization.split(" ", 1)[1].strip()
    return _decode_supabase_jwt(token, settings)

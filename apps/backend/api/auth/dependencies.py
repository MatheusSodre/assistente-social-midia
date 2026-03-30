import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

bearer = HTTPBearer(auto_error=False)

DEV_USER = {
    "sub": "dev-user-001",
    "nome": "Dev User",
    "email": "dev@local.dev",
}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    # Sem token → retorna usuário dev (login desabilitado por enquanto)
    if credentials is None:
        return DEV_USER

    token = credentials.credentials
    secret = os.getenv("JWT_SECRET", "change-me")

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    return payload

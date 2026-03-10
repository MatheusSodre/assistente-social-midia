from fastapi import APIRouter, Depends, HTTPException

from src.db.connection import get_connection

from .dependencies import get_current_user
from .schemas import AuthResponse, GoogleTokenRequest, PerfilUpdate, UsuarioResponse
from .service import create_jwt, upsert_usuario, verify_google_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/google", response_model=AuthResponse)
def login_google(body: GoogleTokenRequest):
    try:
        google_info = verify_google_token(body.token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token Google inválido")

    usuario = upsert_usuario(google_info)
    token = create_jwt(usuario)

    return {
        "access_token": token,
        "usuario": usuario,
    }


@router.get("/me", response_model=UsuarioResponse)
def me(user=Depends(get_current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM usuarios WHERE id = %s", (user["sub"],))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return dict(row)


@router.patch("/perfil", response_model=UsuarioResponse)
def atualizar_perfil(body: PerfilUpdate, user=Depends(get_current_user)):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [user["sub"]]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE usuarios SET {set_clause} WHERE id = %s",
                values,
            )
            cur.execute("SELECT * FROM usuarios WHERE id = %s", (user["sub"],))
            row = cur.fetchone()

    return dict(row)

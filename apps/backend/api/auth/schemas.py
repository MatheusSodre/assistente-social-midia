from pydantic import BaseModel


class GoogleTokenRequest(BaseModel):
    token: str


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    telefone: str | None
    plano: str
    role: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


class PerfilUpdate(BaseModel):
    nome: str | None = None
    telefone: str | None = None

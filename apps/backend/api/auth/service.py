import os
from datetime import datetime, timedelta, timezone

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import jwt

from src.db.connection import get_connection


def verify_google_token(token: str) -> dict:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    info = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
    return info


def upsert_usuario(google_info: dict) -> dict:
    google_sub = google_info["sub"]
    nome = google_info.get("name", "")
    email = google_info.get("email", "")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM usuarios WHERE google_sub = %s", (google_sub,))
            usuario = cur.fetchone()

            if usuario:
                cur.execute(
                    "UPDATE usuarios SET nome = %s, email = %s WHERE google_sub = %s",
                    (nome, email, google_sub),
                )
                cur.execute("SELECT * FROM usuarios WHERE google_sub = %s", (google_sub,))
                usuario = cur.fetchone()
            else:
                cur.execute(
                    "INSERT INTO usuarios (nome, email, google_sub) VALUES (%s, %s, %s)",
                    (nome, email, google_sub),
                )
                cur.execute("SELECT * FROM usuarios WHERE google_sub = %s", (google_sub,))
                usuario = cur.fetchone()

    return dict(usuario)


def create_jwt(usuario: dict) -> str:
    secret = os.getenv("JWT_SECRET", "change-me")
    expire_hours = int(os.getenv("JWT_EXPIRE_HOURS", "720"))
    expire = datetime.now(timezone.utc) + timedelta(hours=expire_hours)

    payload = {
        "sub": usuario["id"],
        "email": usuario["email"],
        "role": usuario["role"],
        "exp": expire,
    }
    return jwt.encode(payload, secret, algorithm="HS256")

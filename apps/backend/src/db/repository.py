"""Queries genéricas/compartilhadas entre módulos."""
from .connection import get_connection


def buscar_usuario_por_id(usuario_id: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM usuarios WHERE id = %s AND ativo = 1",
                (usuario_id,),
            )
            return cur.fetchone()

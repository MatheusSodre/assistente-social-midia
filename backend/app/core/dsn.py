"""
Parsing tolerante de DSN postgres.

Python 3.13 deixou urllib.parse.urlparse mais estrito sobre hostnames
"bracketed" (IPv6). Senhas com caracteres especiais ([, ], !, @, #, etc)
quebram o parser nativo.

Esta função usa rsplit('@') pra separar credenciais do host, e funciona
mesmo quando a senha tem '@' ou colchetes — desde que NÃO tenha ':' antes
do '@' (improvável em senhas geradas pelo Supabase).
"""
from __future__ import annotations

from typing import Any
from urllib.parse import unquote


def parse_postgres_dsn(dsn: str) -> dict[str, Any]:
    """
    Aceita postgresql://user:password@host:port/database[?params]
    Retorna kwargs prontos pra asyncpg.connect/create_pool.
    """
    if dsn.startswith("postgresql://"):
        rest = dsn[len("postgresql://"):]
    elif dsn.startswith("postgres://"):
        rest = dsn[len("postgres://"):]
    else:
        raise ValueError(f"DSN deve começar com postgresql:// — recebido: {dsn[:20]}...")

    creds, _, host_db = rest.rpartition("@")
    if not creds:
        raise ValueError("DSN sem '@' separando credenciais e host")

    user, _, password = creds.partition(":")
    host_part, _, db_part = host_db.partition("/")
    host, _, port_str = host_part.partition(":")

    if "?" in db_part:
        db_part = db_part.split("?", 1)[0]

    # Senha NÃO é decodificada (unquote): usuário escreve literal no .env.
    # rpartition('@') acima já separou corretamente mesmo com '@' na senha.
    return {
        "user": unquote(user) if user else None,
        "password": password if password else None,
        "host": host or None,
        "port": int(port_str) if port_str else 5432,
        "database": db_part or "postgres",
    }

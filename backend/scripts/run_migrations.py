#!/usr/bin/env python3
"""
Migration runner idempotente para o assistente-social-media.

Lê migrations/*.sql em ordem alfabética. Para cada arquivo:
- Verifica em mkt_schema_migrations se já foi aplicado (skip).
- Substitui <<MKT_APP_PASSWORD>> pelo valor de MKT_APP_DB_PASSWORD do .env
  (com escape de aspas simples).
- Executa em uma transação. Se falhar, ROLLBACK + reporta + para.
- Após sucesso, INSERT em mkt_schema_migrations.

Uso:
    cd backend
    python scripts/run_migrations.py

Requer no .env:
    SUPABASE_DB_URL_ADMIN=postgresql://postgres:...   # role com privilégio para CREATE ROLE/EXTENSION
    MKT_APP_DB_PASSWORD=...                           # senha do role mkt_app
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.dsn import parse_postgres_dsn  # noqa: E402


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
SCHEMA_MIGRATIONS_TABLE = "mkt_schema_migrations"
PASSWORD_PLACEHOLDER = "<<MKT_APP_PASSWORD>>"


def log(level: str, msg: str, **fields) -> None:
    payload = {"ts": datetime.now(timezone.utc).isoformat(), "level": level, "msg": msg, **fields}
    print(json.dumps(payload, default=str), flush=True)


def escape_sql_literal(value: str) -> str:
    return value.replace("'", "''")


async def ensure_schema_migrations_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
            filename   text PRIMARY KEY,
            applied_at timestamptz NOT NULL DEFAULT now()
        );
        """
    )


async def already_applied(conn: asyncpg.Connection, filename: str) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA_MIGRATIONS_TABLE} WHERE filename = $1",
        filename,
    )
    return row is not None


async def apply_one(
    conn: asyncpg.Connection,
    path: Path,
    password: str,
) -> None:
    raw = path.read_text(encoding="utf-8")
    sql = raw.replace(PASSWORD_PLACEHOLDER, escape_sql_literal(password))

    async with conn.transaction():
        await conn.execute(sql)
        await conn.execute(
            f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (filename) VALUES ($1)",
            path.name,
        )


async def main() -> int:
    load_dotenv()

    db_url = os.environ.get("SUPABASE_DB_URL_ADMIN")
    password = os.environ.get("MKT_APP_DB_PASSWORD")

    if not db_url:
        log("ERROR", "SUPABASE_DB_URL_ADMIN não definido no .env")
        return 1
    if not password:
        log("ERROR", "MKT_APP_DB_PASSWORD não definido no .env")
        return 1

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        log("ERROR", "Nenhuma migração encontrada", dir=str(MIGRATIONS_DIR))
        return 1

    kwargs = parse_postgres_dsn(db_url)
    log(
        "INFO",
        "Conectando ao banco admin",
        host=kwargs["host"],
        port=kwargs["port"],
        db=kwargs["database"],
        user=kwargs["user"],
        password_len=len(kwargs["password"] or ""),
    )
    conn = await asyncpg.connect(**kwargs)

    try:
        await ensure_schema_migrations_table(conn)

        applied = skipped = 0
        for path in files:
            if await already_applied(conn, path.name):
                log("INFO", "skip (já aplicada)", file=path.name)
                skipped += 1
                continue

            log("INFO", "aplicando", file=path.name)
            try:
                await apply_one(conn, path, password)
            except Exception as exc:
                log("ERROR", "falhou", file=path.name, error=str(exc), error_type=type(exc).__name__)
                return 2
            log("INFO", "ok", file=path.name)
            applied += 1

        log("INFO", "concluído", applied=applied, skipped=skipped, total=len(files))
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

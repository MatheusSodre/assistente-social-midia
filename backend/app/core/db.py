import json
from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import UUID

import asyncpg

from app.core.config import get_settings
from app.core.dsn import parse_postgres_dsn

_pool: asyncpg.Pool | None = None


async def create_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        settings = get_settings()
        kwargs = parse_postgres_dsn(settings.supabase_db_url)
        _pool = await asyncpg.create_pool(
            **kwargs,
            min_size=1,
            max_size=10,
            command_timeout=60,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Pool not initialized. Call create_pool() in lifespan.")
    return _pool


@asynccontextmanager
async def tenant_context(
    pool: asyncpg.Pool,
    tenant_id: UUID,
) -> AsyncIterator[asyncpg.Connection]:
    """
    Abre conexão e transação com request.jwt.claims setado para o tenant_id.
    RLS de mkt_* usa mkt_current_tenant() que lê esse claim.

    Usa set_config(name, value, is_local=true) porque PostgreSQL não aceita
    parameter binding em SET LOCAL.
    """
    claims = json.dumps({"app_metadata": {"tenant_id": str(tenant_id)}})
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                claims,
            )
            yield conn


@asynccontextmanager
async def listen_notify(
    pool: asyncpg.Pool,
    channel: str,
) -> AsyncIterator[asyncpg.Connection]:
    """
    Conexão dedicada em modo LISTEN no canal informado.
    Use conn.add_listener(channel, callback) ou aguarde notifies via add_listener.
    """
    async with pool.acquire() as conn:
        await conn.execute(f"LISTEN {channel}")
        try:
            yield conn
        finally:
            await conn.execute(f"UNLISTEN {channel}")


async def notify(pool: asyncpg.Pool, channel: str, payload: str) -> None:
    """Emite NOTIFY <channel>, '<payload>' fora de tenant_context."""
    async with pool.acquire() as conn:
        await conn.execute("SELECT pg_notify($1, $2)", channel, payload)

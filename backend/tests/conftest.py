from typing import AsyncIterator

import asyncpg
import pytest_asyncio
from dotenv import load_dotenv

from app.core.config import get_settings
from app.core.dsn import parse_postgres_dsn


load_dotenv()


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def db_pool() -> AsyncIterator[asyncpg.Pool]:
    settings = get_settings()
    kwargs = parse_postgres_dsn(settings.supabase_db_url)
    pool = await asyncpg.create_pool(**kwargs, min_size=1, max_size=4)
    yield pool
    await pool.close()

"""Confirma RLS isolando os 7 blocos por tenant nas tabelas novas."""
from uuid import uuid4

import pytest

from app.core.db import tenant_context

TENANT_A = uuid4()
TENANT_B = uuid4()


@pytest.mark.asyncio
async def test_brand_blocks_isolated_by_tenant(db_pool):
    try:
        async with tenant_context(db_pool, TENANT_A) as conn:
            await conn.execute(
                "INSERT INTO mkt_brand_blocks (tenant_id, block_key) VALUES ($1, 'brand')",
                TENANT_A,
            )
        async with tenant_context(db_pool, TENANT_B) as conn:
            await conn.execute(
                "INSERT INTO mkt_brand_blocks (tenant_id, block_key) VALUES ($1, 'brand')",
                TENANT_B,
            )

        async with tenant_context(db_pool, TENANT_A) as conn:
            rows = await conn.fetch(
                "SELECT tenant_id FROM mkt_brand_blocks WHERE block_key = 'brand'"
            )
        assert {r["tenant_id"] for r in rows} == {TENANT_A}

        async with tenant_context(db_pool, TENANT_B) as conn:
            rows = await conn.fetch(
                "SELECT tenant_id FROM mkt_brand_blocks WHERE block_key = 'brand'"
            )
        assert {r["tenant_id"] for r in rows} == {TENANT_B}
    finally:
        async with tenant_context(db_pool, TENANT_A) as conn:
            await conn.execute(
                "DELETE FROM mkt_brand_blocks WHERE tenant_id = $1", TENANT_A
            )
        async with tenant_context(db_pool, TENANT_B) as conn:
            await conn.execute(
                "DELETE FROM mkt_brand_blocks WHERE tenant_id = $1", TENANT_B
            )


@pytest.mark.asyncio
async def test_pending_changes_isolated(db_pool):
    """Cada tenant só enxerga seus próprios pending changes."""
    block_a_id = None
    block_b_id = None
    try:
        async with tenant_context(db_pool, TENANT_A) as conn:
            block_a_id = await conn.fetchval(
                "INSERT INTO mkt_brand_blocks (tenant_id, block_key) "
                "VALUES ($1, 'tone') RETURNING id",
                TENANT_A,
            )
            await conn.execute(
                """
                INSERT INTO mkt_pending_changes
                  (tenant_id, block_id, source_type, source_label, proposed_content, reason)
                VALUES ($1, $2, 'manual', 'teste-A', '{}'::jsonb, 'rls-test-A')
                """,
                TENANT_A, block_a_id,
            )
        async with tenant_context(db_pool, TENANT_B) as conn:
            block_b_id = await conn.fetchval(
                "INSERT INTO mkt_brand_blocks (tenant_id, block_key) "
                "VALUES ($1, 'tone') RETURNING id",
                TENANT_B,
            )
            await conn.execute(
                """
                INSERT INTO mkt_pending_changes
                  (tenant_id, block_id, source_type, source_label, proposed_content, reason)
                VALUES ($1, $2, 'manual', 'teste-B', '{}'::jsonb, 'rls-test-B')
                """,
                TENANT_B, block_b_id,
            )

        async with tenant_context(db_pool, TENANT_A) as conn:
            rows = await conn.fetch(
                "SELECT tenant_id FROM mkt_pending_changes WHERE reason LIKE 'rls-test-%'"
            )
        assert {r["tenant_id"] for r in rows} == {TENANT_A}

        async with tenant_context(db_pool, TENANT_B) as conn:
            rows = await conn.fetch(
                "SELECT tenant_id FROM mkt_pending_changes WHERE reason LIKE 'rls-test-%'"
            )
        assert {r["tenant_id"] for r in rows} == {TENANT_B}
    finally:
        async with tenant_context(db_pool, TENANT_A) as conn:
            await conn.execute(
                "DELETE FROM mkt_pending_changes WHERE tenant_id = $1", TENANT_A
            )
            await conn.execute(
                "DELETE FROM mkt_brand_blocks WHERE tenant_id = $1", TENANT_A
            )
        async with tenant_context(db_pool, TENANT_B) as conn:
            await conn.execute(
                "DELETE FROM mkt_pending_changes WHERE tenant_id = $1", TENANT_B
            )
            await conn.execute(
                "DELETE FROM mkt_brand_blocks WHERE tenant_id = $1", TENANT_B
            )


@pytest.mark.asyncio
async def test_lia_messages_isolated_via_conversation(db_pool):
    """mkt_lia_messages escopa via JOIN — cada tenant só vê suas próprias mensagens."""
    user_a = uuid4()
    user_b = uuid4()
    conv_a_id = None
    conv_b_id = None
    try:
        async with tenant_context(db_pool, TENANT_A) as conn:
            conv_a_id = await conn.fetchval(
                "INSERT INTO mkt_lia_conversations (tenant_id, started_by_user_id) "
                "VALUES ($1, $2) RETURNING id",
                TENANT_A, user_a,
            )
            await conn.execute(
                "INSERT INTO mkt_lia_messages (conversation_id, role, content) "
                "VALUES ($1, 'user', 'msg-A')",
                conv_a_id,
            )
        async with tenant_context(db_pool, TENANT_B) as conn:
            conv_b_id = await conn.fetchval(
                "INSERT INTO mkt_lia_conversations (tenant_id, started_by_user_id) "
                "VALUES ($1, $2) RETURNING id",
                TENANT_B, user_b,
            )
            await conn.execute(
                "INSERT INTO mkt_lia_messages (conversation_id, role, content) "
                "VALUES ($1, 'user', 'msg-B')",
                conv_b_id,
            )

        async with tenant_context(db_pool, TENANT_A) as conn:
            rows = await conn.fetch(
                "SELECT content FROM mkt_lia_messages WHERE content LIKE 'msg-%'"
            )
        assert {r["content"] for r in rows} == {"msg-A"}

        async with tenant_context(db_pool, TENANT_B) as conn:
            rows = await conn.fetch(
                "SELECT content FROM mkt_lia_messages WHERE content LIKE 'msg-%'"
            )
        assert {r["content"] for r in rows} == {"msg-B"}
    finally:
        async with tenant_context(db_pool, TENANT_A) as conn:
            await conn.execute(
                "DELETE FROM mkt_lia_conversations WHERE tenant_id = $1", TENANT_A
            )
        async with tenant_context(db_pool, TENANT_B) as conn:
            await conn.execute(
                "DELETE FROM mkt_lia_conversations WHERE tenant_id = $1", TENANT_B
            )

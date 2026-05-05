"""
Teste-âncora: confirma que set_config('request.jwt.claims', ...) dentro do
tenant_context faz a RLS de mkt_brand_memory isolar tenants. Se este teste
quebra, todo o modelo de segurança do app vai junto.
"""
from uuid import uuid4

import pytest

from app.core.db import tenant_context


TENANT_A = uuid4()
TENANT_B = uuid4()
NAME_A = f"rls-test-A-{TENANT_A}"
NAME_B = f"rls-test-B-{TENANT_B}"


@pytest.mark.asyncio
async def test_brand_memory_isolated_by_tenant(db_pool):
    try:
        async with tenant_context(db_pool, TENANT_A) as conn:
            await conn.execute(
                "INSERT INTO mkt_brand_memory (tenant_id, name) VALUES ($1, $2)",
                TENANT_A, NAME_A,
            )
        async with tenant_context(db_pool, TENANT_B) as conn:
            await conn.execute(
                "INSERT INTO mkt_brand_memory (tenant_id, name) VALUES ($1, $2)",
                TENANT_B, NAME_B,
            )

        async with tenant_context(db_pool, TENANT_A) as conn:
            rows = await conn.fetch(
                "SELECT name FROM mkt_brand_memory WHERE name LIKE 'rls-test-%'"
            )
        seen_a = {r["name"] for r in rows}
        assert seen_a == {NAME_A}, f"Tenant A deveria ver só A, viu: {seen_a}"

        async with tenant_context(db_pool, TENANT_B) as conn:
            rows = await conn.fetch(
                "SELECT name FROM mkt_brand_memory WHERE name LIKE 'rls-test-%'"
            )
        seen_b = {r["name"] for r in rows}
        assert seen_b == {NAME_B}, f"Tenant B deveria ver só B, viu: {seen_b}"

    finally:
        # cleanup: usa cada tenant_context pra deletar suas próprias linhas
        async with tenant_context(db_pool, TENANT_A) as conn:
            await conn.execute(
                "DELETE FROM mkt_brand_memory WHERE name = $1", NAME_A
            )
        async with tenant_context(db_pool, TENANT_B) as conn:
            await conn.execute(
                "DELETE FROM mkt_brand_memory WHERE name = $1", NAME_B
            )


@pytest.mark.asyncio
async def test_insert_with_wrong_tenant_id_blocked(db_pool):
    """RLS WITH CHECK deve bloquear INSERT com tenant_id != mkt_current_tenant()."""
    other = uuid4()
    async with tenant_context(db_pool, TENANT_A) as conn:
        with pytest.raises(Exception):
            await conn.execute(
                "INSERT INTO mkt_brand_memory (tenant_id, name) VALUES ($1, $2)",
                other, "should-fail",
            )

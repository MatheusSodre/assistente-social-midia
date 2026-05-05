"""
Fluxo end-to-end: propose → accept → version criada → revert → version_number incrementa.
Usa BrandBlockService + ChangeService diretos (sem HTTP) pra testar a lógica
de governança ponta-a-ponta.
"""
from uuid import uuid4

import pytest

from app.core.db import tenant_context
from app.models.brand_block import BlockKey, ChangeSourceType
from app.models.pending_change import PendingChangeCreate, PendingChangeStatus
from app.services.brand_block_service import BrandBlockService
from app.services.change_service import ChangeService


TENANT = uuid4()
USER = uuid4()


@pytest.mark.asyncio
async def test_propose_accept_revert_flow(db_pool):
    block_service = BrandBlockService(db_pool)
    change_service = ChangeService(db_pool, block_service)

    try:
        # ---------- 1. dashboard cria 7 blocos vazios na primeira leitura
        dashboard = await block_service.get_dashboard(tenant_id=TENANT)
        assert len(dashboard.blocks) == 7
        assert dashboard.completion_pct == 0
        assert dashboard.pending_changes_count == 0

        # ---------- 1b. seed `examples` com versão pra cascade ter conteúdo
        # de origem (cascade só dispara quando target tem current_version).
        examples_seed = await change_service.propose(
            tenant_id=TENANT,
            proposed_by_user_id=USER,
            payload=PendingChangeCreate(
                block_key=BlockKey.EXAMPLES,
                proposed_content={"items": [{"caption": "post antigo"}]},
                reason="seed",
                source_type=ChangeSourceType.MANUAL,
                source_label="seed",
            ),
        )
        await change_service.accept(
            tenant_id=TENANT,
            change_id=examples_seed.id,
            resolved_by_user_id=USER,
        )

        # ---------- 2. propõe mudança em 'tone'
        payload = PendingChangeCreate(
            block_key=BlockKey.TONE,
            proposed_content={
                "style": "Direto, técnico-pragmático",
                "do": ["usar você", "tomar posição"],
                "dont": ["corporativês"],
                "examples": [],
            },
            reason="Definindo voz inicial",
            source_type=ChangeSourceType.MANUAL,
            source_label="edição manual",
        )
        change = await change_service.propose(
            tenant_id=TENANT,
            proposed_by_user_id=USER,
            payload=payload,
        )
        assert change.status == PendingChangeStatus.PENDING
        assert change.block_key == BlockKey.TONE
        assert change.from_version_id is None  # primeiro change desse bloco
        # tone tem cascade pra examples (regra seedada em 013)
        assert any(c.block_key == BlockKey.EXAMPLES for c in change.cascades)

        change_id = change.id

        # ---------- 3. aceita
        accepted = await change_service.accept(
            tenant_id=TENANT,
            change_id=change_id,
            resolved_by_user_id=USER,
        )
        assert accepted.status == PendingChangeStatus.ACCEPTED
        assert accepted.resolved_by_user_id == USER
        assert accepted.resolved_at is not None

        # ---------- 4. version criada (v1) e ponteiro atualizado
        block = await block_service.get_block(tenant_id=TENANT, block_key=BlockKey.TONE)
        assert block is not None
        assert block.version_number == 1
        assert block.content["style"] == "Direto, técnico-pragmático"
        assert block.confidence > 0
        assert block.status.value in ("partial", "complete")

        versions = await block_service.list_versions(
            tenant_id=TENANT, block_key=BlockKey.TONE
        )
        assert len(versions) == 1
        assert versions[0].version_number == 1
        assert versions[0].source_type == ChangeSourceType.MANUAL

        # ---------- 5. cascade gerou pending_change filha em 'examples'
        pending = await change_service.list_pending(tenant_id=TENANT)
        cascade_children = [
            c for c in pending
            if c.proposed_by_agent == "cascade" and c.block_key == BlockKey.EXAMPLES
        ]
        assert len(cascade_children) >= 1, "cascade pra examples não foi gerada"

        # ---------- 6. propõe segunda mudança em 'tone' e aceita
        payload_v2 = PendingChangeCreate(
            block_key=BlockKey.TONE,
            proposed_content={
                "style": "Direto e generoso",
                "do": ["usar você", "tomar posição", "ser específico"],
                "dont": ["corporativês", "emojis decorativos"],
                "examples": [],
            },
            reason="Refinando voz",
            source_type=ChangeSourceType.MANUAL,
            source_label="edição manual",
        )
        change_v2 = await change_service.propose(
            tenant_id=TENANT,
            proposed_by_user_id=USER,
            payload=payload_v2,
        )
        # agora from_version aponta pra v1
        assert change_v2.from_version_id is not None
        assert change_v2.from_version_number == 1

        await change_service.accept(
            tenant_id=TENANT, change_id=change_v2.id, resolved_by_user_id=USER
        )

        block_v2 = await block_service.get_block(tenant_id=TENANT, block_key=BlockKey.TONE)
        assert block_v2.version_number == 2

        # ---------- 7. revert pra v1 → cria v3 com conteúdo de v1
        block_after_revert = await block_service.revert_to_version(
            tenant_id=TENANT, block_key=BlockKey.TONE, version_number=1
        )
        assert block_after_revert.version_number == 3
        assert block_after_revert.content["style"] == "Direto, técnico-pragmático"

        versions_after = await block_service.list_versions(
            tenant_id=TENANT, block_key=BlockKey.TONE
        )
        # v3 (revert), v2 (refinar), v1 (inicial)
        assert [v.version_number for v in versions_after] == [3, 2, 1]
        assert versions_after[0].source_ref == "revert from v1"
    finally:
        # cleanup: remove blocks (cascade leva versions e pending_changes juntos)
        async with tenant_context(db_pool, TENANT) as conn:
            await conn.execute("DELETE FROM mkt_brand_blocks WHERE tenant_id = $1", TENANT)


@pytest.mark.asyncio
async def test_invalid_content_returns_validation_error(db_pool):
    """Conteúdo fora do schema do bloco deve falhar validação."""
    block_service = BrandBlockService(db_pool)
    change_service = ChangeService(db_pool, block_service)

    try:
        await block_service.get_dashboard(tenant_id=TENANT)  # bootstrap

        # ICP exige `personas: list[IcpPersona]` — passar string deve quebrar
        with pytest.raises(Exception):
            await change_service.propose(
                tenant_id=TENANT,
                proposed_by_user_id=USER,
                payload=PendingChangeCreate(
                    block_key=BlockKey.ICP,
                    proposed_content={"personas": "not a list"},
                    reason="bad content",
                    source_type=ChangeSourceType.MANUAL,
                    source_label="test",
                ),
            )
    finally:
        async with tenant_context(db_pool, TENANT) as conn:
            await conn.execute("DELETE FROM mkt_brand_blocks WHERE tenant_id = $1", TENANT)


@pytest.mark.asyncio
async def test_reject_does_not_create_version(db_pool):
    block_service = BrandBlockService(db_pool)
    change_service = ChangeService(db_pool, block_service)

    try:
        await block_service.get_dashboard(tenant_id=TENANT)

        change = await change_service.propose(
            tenant_id=TENANT,
            proposed_by_user_id=USER,
            payload=PendingChangeCreate(
                block_key=BlockKey.VISUAL,
                proposed_content={"primary_color": "#ff0000"},
                reason="cor errada",
                source_type=ChangeSourceType.MANUAL,
                source_label="manual",
            ),
        )

        rejected = await change_service.reject(
            tenant_id=TENANT, change_id=change.id, resolved_by_user_id=USER
        )
        assert rejected.status == PendingChangeStatus.REJECTED

        versions = await block_service.list_versions(
            tenant_id=TENANT, block_key=BlockKey.VISUAL
        )
        assert len(versions) == 0
    finally:
        async with tenant_context(db_pool, TENANT) as conn:
            await conn.execute("DELETE FROM mkt_brand_blocks WHERE tenant_id = $1", TENANT)

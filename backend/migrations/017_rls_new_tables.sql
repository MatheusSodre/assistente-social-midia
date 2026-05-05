-- ============================================================================
-- RLS para as 7 tabelas novas de governança do Brand Memory.
-- Mesmo padrão de 008_rls_policies.sql: mkt_app é NOBYPASSRLS, tenant_context
-- seta JWT claim, policies usam mkt_current_tenant().
-- ============================================================================

-- ---------------------------------------------------------------------------
-- mkt_brand_blocks
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_brand_blocks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_brand_blocks_select ON mkt_brand_blocks;
DROP POLICY IF EXISTS mkt_brand_blocks_modify ON mkt_brand_blocks;

CREATE POLICY mkt_brand_blocks_select ON mkt_brand_blocks
  FOR SELECT USING (tenant_id = mkt_current_tenant());

CREATE POLICY mkt_brand_blocks_modify ON mkt_brand_blocks
  FOR ALL USING (tenant_id = mkt_current_tenant())
  WITH CHECK (tenant_id = mkt_current_tenant());

-- ---------------------------------------------------------------------------
-- mkt_brand_block_versions — escopo via JOIN em block
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_brand_block_versions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_brand_block_versions_select ON mkt_brand_block_versions;
DROP POLICY IF EXISTS mkt_brand_block_versions_modify ON mkt_brand_block_versions;

CREATE POLICY mkt_brand_block_versions_select ON mkt_brand_block_versions
  FOR SELECT USING (EXISTS (
    SELECT 1 FROM mkt_brand_blocks b
    WHERE b.id = mkt_brand_block_versions.block_id
      AND b.tenant_id = mkt_current_tenant()
  ));

CREATE POLICY mkt_brand_block_versions_modify ON mkt_brand_block_versions
  FOR ALL USING (EXISTS (
    SELECT 1 FROM mkt_brand_blocks b
    WHERE b.id = mkt_brand_block_versions.block_id
      AND b.tenant_id = mkt_current_tenant()
  )) WITH CHECK (EXISTS (
    SELECT 1 FROM mkt_brand_blocks b
    WHERE b.id = mkt_brand_block_versions.block_id
      AND b.tenant_id = mkt_current_tenant()
  ));

-- ---------------------------------------------------------------------------
-- mkt_pending_changes
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_pending_changes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_pending_changes_select ON mkt_pending_changes;
DROP POLICY IF EXISTS mkt_pending_changes_modify ON mkt_pending_changes;

CREATE POLICY mkt_pending_changes_select ON mkt_pending_changes
  FOR SELECT USING (tenant_id = mkt_current_tenant());

CREATE POLICY mkt_pending_changes_modify ON mkt_pending_changes
  FOR ALL USING (tenant_id = mkt_current_tenant())
  WITH CHECK (tenant_id = mkt_current_tenant());

-- ---------------------------------------------------------------------------
-- mkt_change_cascades — leitura pública (regras globais), modificação só
-- admin via SQL direto (BYPASSRLS).
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_change_cascades ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_change_cascades_select ON mkt_change_cascades;

CREATE POLICY mkt_change_cascades_select ON mkt_change_cascades
  FOR SELECT USING (true);

-- ---------------------------------------------------------------------------
-- mkt_sources
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_sources ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_sources_select ON mkt_sources;
DROP POLICY IF EXISTS mkt_sources_modify ON mkt_sources;

CREATE POLICY mkt_sources_select ON mkt_sources
  FOR SELECT USING (tenant_id = mkt_current_tenant());

CREATE POLICY mkt_sources_modify ON mkt_sources
  FOR ALL USING (tenant_id = mkt_current_tenant())
  WITH CHECK (tenant_id = mkt_current_tenant());

-- ---------------------------------------------------------------------------
-- mkt_lia_conversations
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_lia_conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_lia_conversations_select ON mkt_lia_conversations;
DROP POLICY IF EXISTS mkt_lia_conversations_modify ON mkt_lia_conversations;

CREATE POLICY mkt_lia_conversations_select ON mkt_lia_conversations
  FOR SELECT USING (tenant_id = mkt_current_tenant());

CREATE POLICY mkt_lia_conversations_modify ON mkt_lia_conversations
  FOR ALL USING (tenant_id = mkt_current_tenant())
  WITH CHECK (tenant_id = mkt_current_tenant());

-- ---------------------------------------------------------------------------
-- mkt_lia_messages — escopo via JOIN em conversation
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_lia_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_lia_messages_select ON mkt_lia_messages;
DROP POLICY IF EXISTS mkt_lia_messages_modify ON mkt_lia_messages;

CREATE POLICY mkt_lia_messages_select ON mkt_lia_messages
  FOR SELECT USING (EXISTS (
    SELECT 1 FROM mkt_lia_conversations c
    WHERE c.id = mkt_lia_messages.conversation_id
      AND c.tenant_id = mkt_current_tenant()
  ));

CREATE POLICY mkt_lia_messages_modify ON mkt_lia_messages
  FOR ALL USING (EXISTS (
    SELECT 1 FROM mkt_lia_conversations c
    WHERE c.id = mkt_lia_messages.conversation_id
      AND c.tenant_id = mkt_current_tenant()
  )) WITH CHECK (EXISTS (
    SELECT 1 FROM mkt_lia_conversations c
    WHERE c.id = mkt_lia_messages.conversation_id
      AND c.tenant_id = mkt_current_tenant()
  ));

-- ============================================================================
-- RLS: rede de segurança no banco. Backend conecta como mkt_app (NOBYPASSRLS)
-- e seta request.jwt.claims via set_config dentro de tenant_context.
-- ============================================================================

CREATE OR REPLACE FUNCTION mkt_current_tenant() RETURNS uuid AS $$
  SELECT NULLIF(
    current_setting('request.jwt.claims', true)::jsonb #>> '{app_metadata,tenant_id}',
    ''
  )::uuid
$$ LANGUAGE sql STABLE;

GRANT EXECUTE ON FUNCTION mkt_current_tenant() TO mkt_app;

-- ---------------------------------------------------------------------------
-- mkt_brand_memory
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_brand_memory ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_brand_memory_select ON mkt_brand_memory;
DROP POLICY IF EXISTS mkt_brand_memory_modify ON mkt_brand_memory;

CREATE POLICY mkt_brand_memory_select ON mkt_brand_memory
  FOR SELECT
  USING (tenant_id = mkt_current_tenant());

CREATE POLICY mkt_brand_memory_modify ON mkt_brand_memory
  FOR ALL
  USING (tenant_id = mkt_current_tenant())
  WITH CHECK (tenant_id = mkt_current_tenant());

-- ---------------------------------------------------------------------------
-- mkt_generations
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_generations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_generations_select ON mkt_generations;
DROP POLICY IF EXISTS mkt_generations_modify ON mkt_generations;

CREATE POLICY mkt_generations_select ON mkt_generations
  FOR SELECT
  USING (tenant_id = mkt_current_tenant());

CREATE POLICY mkt_generations_modify ON mkt_generations
  FOR ALL
  USING (tenant_id = mkt_current_tenant())
  WITH CHECK (tenant_id = mkt_current_tenant());

-- ---------------------------------------------------------------------------
-- mkt_assets — escopo via JOIN em mkt_generations.tenant_id
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_assets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_assets_select ON mkt_assets;
DROP POLICY IF EXISTS mkt_assets_modify ON mkt_assets;

CREATE POLICY mkt_assets_select ON mkt_assets
  FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM mkt_generations g
    WHERE g.id = mkt_assets.generation_id
      AND g.tenant_id = mkt_current_tenant()
  ));

CREATE POLICY mkt_assets_modify ON mkt_assets
  FOR ALL
  USING (EXISTS (
    SELECT 1 FROM mkt_generations g
    WHERE g.id = mkt_assets.generation_id
      AND g.tenant_id = mkt_current_tenant()
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM mkt_generations g
    WHERE g.id = mkt_assets.generation_id
      AND g.tenant_id = mkt_current_tenant()
  ));

-- ---------------------------------------------------------------------------
-- mkt_agent_logs — mesmo padrão (escopo via generation)
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_agent_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_agent_logs_select ON mkt_agent_logs;
DROP POLICY IF EXISTS mkt_agent_logs_modify ON mkt_agent_logs;

CREATE POLICY mkt_agent_logs_select ON mkt_agent_logs
  FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM mkt_generations g
    WHERE g.id = mkt_agent_logs.generation_id
      AND g.tenant_id = mkt_current_tenant()
  ));

CREATE POLICY mkt_agent_logs_modify ON mkt_agent_logs
  FOR ALL
  USING (EXISTS (
    SELECT 1 FROM mkt_generations g
    WHERE g.id = mkt_agent_logs.generation_id
      AND g.tenant_id = mkt_current_tenant()
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM mkt_generations g
    WHERE g.id = mkt_agent_logs.generation_id
      AND g.tenant_id = mkt_current_tenant()
  ));

-- ---------------------------------------------------------------------------
-- mkt_templates — leitura pública (não tem tenant)
-- ---------------------------------------------------------------------------
ALTER TABLE mkt_templates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mkt_templates_select ON mkt_templates;
CREATE POLICY mkt_templates_select ON mkt_templates
  FOR SELECT
  USING (true);

-- ---------------------------------------------------------------------------
-- Storage policies: convenção {bucket}/{tenant_id}/{generation_id}/{file}
-- ---------------------------------------------------------------------------
DROP POLICY IF EXISTS mkt_storage_brand_assets_read ON storage.objects;
CREATE POLICY mkt_storage_brand_assets_read ON storage.objects
  FOR SELECT
  USING (
    bucket_id = 'mkt-brand-assets'
    AND (storage.foldername(name))[1] = mkt_current_tenant()::text
  );

DROP POLICY IF EXISTS mkt_storage_brand_assets_write ON storage.objects;
CREATE POLICY mkt_storage_brand_assets_write ON storage.objects
  FOR ALL
  USING (
    bucket_id = 'mkt-brand-assets'
    AND (storage.foldername(name))[1] = mkt_current_tenant()::text
  )
  WITH CHECK (
    bucket_id = 'mkt-brand-assets'
    AND (storage.foldername(name))[1] = mkt_current_tenant()::text
  );

DROP POLICY IF EXISTS mkt_storage_generations_read ON storage.objects;
CREATE POLICY mkt_storage_generations_read ON storage.objects
  FOR SELECT
  USING (
    bucket_id = 'mkt-generations'
    AND (storage.foldername(name))[1] = mkt_current_tenant()::text
  );

DROP POLICY IF EXISTS mkt_storage_exports_read ON storage.objects;
CREATE POLICY mkt_storage_exports_read ON storage.objects
  FOR SELECT
  USING (
    bucket_id = 'mkt-exports'
    AND (storage.foldername(name))[1] = mkt_current_tenant()::text
  );

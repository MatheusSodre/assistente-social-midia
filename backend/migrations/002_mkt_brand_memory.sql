CREATE OR REPLACE FUNCTION mkt_set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS mkt_brand_memory (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       uuid NOT NULL,
  name            text NOT NULL,
  positioning     text,
  icp             jsonb NOT NULL DEFAULT '[]'::jsonb,
  tone_of_voice   jsonb NOT NULL DEFAULT '{}'::jsonb,
  visual_identity jsonb NOT NULL DEFAULT '{}'::jsonb,
  pillars         text[] NOT NULL DEFAULT '{}',
  competitors     jsonb NOT NULL DEFAULT '[]'::jsonb,
  examples        jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mkt_brand_memory_tenant_idx
  ON mkt_brand_memory(tenant_id);

DROP TRIGGER IF EXISTS mkt_brand_memory_updated_at ON mkt_brand_memory;
CREATE TRIGGER mkt_brand_memory_updated_at
  BEFORE UPDATE ON mkt_brand_memory
  FOR EACH ROW EXECUTE FUNCTION mkt_set_updated_at();

DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_brand_block_key') THEN
    CREATE TYPE mkt_brand_block_key AS ENUM (
      'brand', 'icp', 'tone', 'visual', 'topics', 'competitors', 'examples'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_block_status') THEN
    CREATE TYPE mkt_block_status AS ENUM ('complete', 'partial', 'empty');
  END IF;
END
$do$;

CREATE TABLE IF NOT EXISTS mkt_brand_blocks (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           uuid NOT NULL,
  block_key           mkt_brand_block_key NOT NULL,
  current_version_id  uuid,  -- FK adicionada depois pra evitar circular
  status              mkt_block_status NOT NULL DEFAULT 'empty',
  confidence          smallint NOT NULL DEFAULT 0 CHECK (confidence BETWEEN 0 AND 100),
  source_label        text,  -- ex: "Site + 38 posts"
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, block_key)
);

CREATE INDEX IF NOT EXISTS mkt_brand_blocks_tenant_idx ON mkt_brand_blocks(tenant_id);

DROP TRIGGER IF EXISTS mkt_brand_blocks_updated_at ON mkt_brand_blocks;
CREATE TRIGGER mkt_brand_blocks_updated_at
  BEFORE UPDATE ON mkt_brand_blocks
  FOR EACH ROW EXECUTE FUNCTION mkt_set_updated_at();

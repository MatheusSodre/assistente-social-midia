DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_asset_type') THEN
    CREATE TYPE mkt_asset_type AS ENUM ('image_png', 'carousel_zip', 'copy_text');
  END IF;
END
$do$;

CREATE TABLE IF NOT EXISTS mkt_assets (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  generation_id uuid NOT NULL REFERENCES mkt_generations(id) ON DELETE CASCADE,
  type          mkt_asset_type NOT NULL,
  storage_path  text NOT NULL,
  metadata      jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mkt_assets_generation_idx
  ON mkt_assets(generation_id);

-- Index funcional pra cache de imagem do VisualAgent (lookup por sha256)
CREATE INDEX IF NOT EXISTS mkt_assets_cache_hash_idx
  ON mkt_assets((metadata->>'cache_hash'))
  WHERE metadata ? 'cache_hash';

DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_change_source_type') THEN
    CREATE TYPE mkt_change_source_type AS ENUM (
      'manual', 'session', 'cascade', 'ingestion', 'lia', 'system'
    );
  END IF;
END
$do$;

CREATE TABLE IF NOT EXISTS mkt_brand_block_versions (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  block_id        uuid NOT NULL REFERENCES mkt_brand_blocks(id) ON DELETE CASCADE,
  version_number  int NOT NULL,
  content         jsonb NOT NULL,
  source_type     mkt_change_source_type NOT NULL,
  source_ref      text,        -- conversation_id, fonte_id, "user manual edit", etc.
  created_by      uuid,        -- user_id ou null se foi system/agent
  created_by_agent text,       -- 'lia', 'vega', null se humano
  reason          text,        -- justificativa da mudança
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (block_id, version_number)
);

CREATE INDEX IF NOT EXISTS mkt_brand_block_versions_block_idx
  ON mkt_brand_block_versions(block_id, version_number DESC);

-- FK circular agora que versions existe
DO $fk$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'mkt_brand_blocks_current_version_fk'
  ) THEN
    ALTER TABLE mkt_brand_blocks
      ADD CONSTRAINT mkt_brand_blocks_current_version_fk
      FOREIGN KEY (current_version_id) REFERENCES mkt_brand_block_versions(id)
      ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
  END IF;
END
$fk$;

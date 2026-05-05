DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_pending_change_status') THEN
    CREATE TYPE mkt_pending_change_status AS ENUM (
      'pending', 'accepted', 'rejected', 'superseded'
    );
  END IF;
END
$do$;

CREATE TABLE IF NOT EXISTS mkt_pending_changes (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             uuid NOT NULL,
  block_id              uuid NOT NULL REFERENCES mkt_brand_blocks(id) ON DELETE CASCADE,
  proposed_by_user_id   uuid,
  proposed_by_agent     text,           -- 'lia', 'vega', 'cascade', null se manual
  source_type           mkt_change_source_type NOT NULL,
  source_label          text NOT NULL,  -- "sessão · você aceitou", "ingestão pdf", etc.
  source_ref            text,
  from_version_id       uuid REFERENCES mkt_brand_block_versions(id) ON DELETE SET NULL,
  proposed_content      jsonb NOT NULL,
  reason                text NOT NULL CHECK (length(reason) <= 200),
  cascades              jsonb NOT NULL DEFAULT '[]'::jsonb,  -- array de {block_key, hint}
  status                mkt_pending_change_status NOT NULL DEFAULT 'pending',
  resolved_by_user_id   uuid,
  resolved_at           timestamptz,
  created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mkt_pending_changes_tenant_idx ON mkt_pending_changes(tenant_id);
CREATE INDEX IF NOT EXISTS mkt_pending_changes_block_idx ON mkt_pending_changes(block_id);
CREATE INDEX IF NOT EXISTS mkt_pending_changes_status_idx ON mkt_pending_changes(status)
  WHERE status = 'pending';

DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_lia_message_role') THEN
    CREATE TYPE mkt_lia_message_role AS ENUM (
      'user', 'lia', 'tool_use', 'tool_result'
    );
  END IF;
END
$do$;

CREATE TABLE IF NOT EXISTS mkt_lia_messages (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id   uuid NOT NULL REFERENCES mkt_lia_conversations(id) ON DELETE CASCADE,
  role              mkt_lia_message_role NOT NULL,
  content           text,                -- texto da mensagem (user, lia)
  tool_name         text,                -- 'propose_brand_memory_change', etc.
  tool_input        jsonb,
  tool_use_id       text,                -- id de correlação tool_use ↔ tool_result
  tool_result       jsonb,
  model             text,                -- 'haiku-4-5' ou 'sonnet-4-6'
  tokens_in         int NOT NULL DEFAULT 0,
  tokens_out        int NOT NULL DEFAULT 0,
  cost_cents        int NOT NULL DEFAULT 0,
  latency_ms        int,
  created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mkt_lia_messages_conversation_idx
  ON mkt_lia_messages(conversation_id, created_at);

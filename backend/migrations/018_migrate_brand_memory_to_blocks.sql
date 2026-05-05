-- IDEMPOTENTE: só migra tenants que ainda não têm blocks criados.
-- Roda uma vez via run_migrations.py e fim — depois disso é no-op.
-- mkt_brand_memory original NÃO é dropada aqui — fica como ouro de lastro
-- até PROMPT 02.6 confirmar que tudo funciona.

DO $migrate$
DECLARE
  bm RECORD;
  block_id uuid;
  version_id uuid;
  block_content jsonb;
  block_status mkt_block_status;
  block_confidence smallint;
BEGIN
  FOR bm IN
    SELECT * FROM mkt_brand_memory
    WHERE NOT EXISTS (
      SELECT 1 FROM mkt_brand_blocks b
      WHERE b.tenant_id = mkt_brand_memory.tenant_id
    )
  LOOP
    -- BLOCK: brand
    block_content := jsonb_build_object(
      'name', bm.name,
      'positioning', bm.positioning,
      'pillars', to_jsonb(bm.pillars)
    );
    block_status := CASE
      WHEN bm.positioning IS NOT NULL AND bm.positioning != '' THEN 'partial'::mkt_block_status
      ELSE 'empty'::mkt_block_status
    END;
    block_confidence := CASE WHEN block_status = 'partial' THEN 60 ELSE 0 END;

    INSERT INTO mkt_brand_blocks (tenant_id, block_key, status, confidence, source_label)
    VALUES (bm.tenant_id, 'brand', block_status, block_confidence, 'migração legacy')
    RETURNING id INTO block_id;

    INSERT INTO mkt_brand_block_versions (block_id, version_number, content, source_type, reason)
    VALUES (block_id, 1, block_content, 'system', 'migração inicial de mkt_brand_memory')
    RETURNING id INTO version_id;

    UPDATE mkt_brand_blocks SET current_version_id = version_id WHERE id = block_id;

    -- BLOCK: icp
    block_content := bm.icp;
    block_status := CASE
      WHEN jsonb_array_length(bm.icp) > 0 THEN 'partial'::mkt_block_status
      ELSE 'empty'::mkt_block_status
    END;
    block_confidence := CASE WHEN block_status = 'partial' THEN 50 ELSE 0 END;

    INSERT INTO mkt_brand_blocks (tenant_id, block_key, status, confidence, source_label)
    VALUES (bm.tenant_id, 'icp', block_status, block_confidence, 'migração legacy')
    RETURNING id INTO block_id;

    INSERT INTO mkt_brand_block_versions (block_id, version_number, content, source_type, reason)
    VALUES (block_id, 1, block_content, 'system', 'migração inicial de mkt_brand_memory')
    RETURNING id INTO version_id;

    UPDATE mkt_brand_blocks SET current_version_id = version_id WHERE id = block_id;

    -- BLOCK: tone
    block_content := bm.tone_of_voice;
    block_status := CASE
      WHEN bm.tone_of_voice ? 'style' AND bm.tone_of_voice->>'style' IS NOT NULL
        THEN 'partial'::mkt_block_status
      ELSE 'empty'::mkt_block_status
    END;
    block_confidence := CASE WHEN block_status = 'partial' THEN 70 ELSE 0 END;

    INSERT INTO mkt_brand_blocks (tenant_id, block_key, status, confidence, source_label)
    VALUES (bm.tenant_id, 'tone', block_status, block_confidence, 'migração legacy')
    RETURNING id INTO block_id;

    INSERT INTO mkt_brand_block_versions (block_id, version_number, content, source_type, reason)
    VALUES (block_id, 1, block_content, 'system', 'migração inicial de mkt_brand_memory')
    RETURNING id INTO version_id;

    UPDATE mkt_brand_blocks SET current_version_id = version_id WHERE id = block_id;

    -- BLOCK: visual
    block_content := bm.visual_identity;
    block_status := CASE
      WHEN bm.visual_identity ? 'primary_color' THEN 'partial'::mkt_block_status
      ELSE 'empty'::mkt_block_status
    END;
    block_confidence := CASE WHEN block_status = 'partial' THEN 80 ELSE 0 END;

    INSERT INTO mkt_brand_blocks (tenant_id, block_key, status, confidence, source_label)
    VALUES (bm.tenant_id, 'visual', block_status, block_confidence, 'migração legacy')
    RETURNING id INTO block_id;

    INSERT INTO mkt_brand_block_versions (block_id, version_number, content, source_type, reason)
    VALUES (block_id, 1, block_content, 'system', 'migração inicial de mkt_brand_memory')
    RETURNING id INTO version_id;

    UPDATE mkt_brand_blocks SET current_version_id = version_id WHERE id = block_id;

    -- BLOCK: topics (era pillars no schema antigo, sobe pro bloco próprio)
    block_content := jsonb_build_object('pillars', to_jsonb(bm.pillars));
    block_status := CASE
      WHEN array_length(bm.pillars, 1) > 0 THEN 'partial'::mkt_block_status
      ELSE 'empty'::mkt_block_status
    END;
    block_confidence := CASE WHEN block_status = 'partial' THEN 75 ELSE 0 END;

    INSERT INTO mkt_brand_blocks (tenant_id, block_key, status, confidence, source_label)
    VALUES (bm.tenant_id, 'topics', block_status, block_confidence, 'migração legacy')
    RETURNING id INTO block_id;

    INSERT INTO mkt_brand_block_versions (block_id, version_number, content, source_type, reason)
    VALUES (block_id, 1, block_content, 'system', 'migração inicial de mkt_brand_memory')
    RETURNING id INTO version_id;

    UPDATE mkt_brand_blocks SET current_version_id = version_id WHERE id = block_id;

    -- BLOCK: competitors
    block_content := bm.competitors;
    block_status := CASE
      WHEN jsonb_array_length(bm.competitors) > 0 THEN 'partial'::mkt_block_status
      ELSE 'empty'::mkt_block_status
    END;
    block_confidence := CASE WHEN block_status = 'partial' THEN 50 ELSE 0 END;

    INSERT INTO mkt_brand_blocks (tenant_id, block_key, status, confidence, source_label)
    VALUES (bm.tenant_id, 'competitors', block_status, block_confidence, 'migração legacy')
    RETURNING id INTO block_id;

    INSERT INTO mkt_brand_block_versions (block_id, version_number, content, source_type, reason)
    VALUES (block_id, 1, block_content, 'system', 'migração inicial de mkt_brand_memory')
    RETURNING id INTO version_id;

    UPDATE mkt_brand_blocks SET current_version_id = version_id WHERE id = block_id;

    -- BLOCK: examples
    block_content := bm.examples;
    block_status := CASE
      WHEN jsonb_array_length(bm.examples) > 0 THEN 'partial'::mkt_block_status
      ELSE 'empty'::mkt_block_status
    END;
    block_confidence := CASE WHEN block_status = 'partial' THEN 60 ELSE 0 END;

    INSERT INTO mkt_brand_blocks (tenant_id, block_key, status, confidence, source_label)
    VALUES (bm.tenant_id, 'examples', block_status, block_confidence, 'migração legacy')
    RETURNING id INTO block_id;

    INSERT INTO mkt_brand_block_versions (block_id, version_number, content, source_type, reason)
    VALUES (block_id, 1, block_content, 'system', 'migração inicial de mkt_brand_memory')
    RETURNING id INTO version_id;

    UPDATE mkt_brand_blocks SET current_version_id = version_id WHERE id = block_id;

  END LOOP;
END
$migrate$;

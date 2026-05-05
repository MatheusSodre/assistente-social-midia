# Visual Agent — referência interna

Este arquivo NÃO é system prompt de LLM. O Visual Agent não chama LLM —
chama um ImageProvider (Gemini Flash Image) com um prompt construído.

## Inputs
- visual_brief (do Content Agent)
- brand.visual_identity (style_description, primary_color, secondary_color, logo_url, fonts)
- template.dimensions (width × height)
- template.id (entra no cache_hash)

## Construção do prompt enviado ao ImageProvider
1. visual_brief (1ª linha; linha em branco depois)
2. "Style: <visual_identity.style_description>" (se existir)
3. "Color palette: <primary_color>, <secondary_color>" (se existirem)
4. "Output format: photographic image, <width>x<height> pixels, aspect ratio <ratio>.
   No text, no captions, no watermarks."

## Cache
- cache_hash = sha256(visual_brief + json(visual_identity, sort_keys=True) + str(template_id))
- Lookup em mkt_assets WHERE metadata->>'cache_hash' = cache_hash AND type='image_png'
- Hit → reutiliza storage_path, não chama Gemini
- Miss → gera, faz upload, registra em mkt_assets com metadata.cache_hash

## Storage
- Bucket: mkt-generations
- Path: {tenant_id}/{generation_id}/background.png

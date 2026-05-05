-- 5 templates iniciais. Layout em JSON é placeholder razoável; refino em iteração.

INSERT INTO mkt_templates (name, type, dimensions, slots, layout_config) VALUES
(
  'Post Quadrado Padrão', 'post',
  '{"width":1080,"height":1080}'::jsonb,
  $$
  {
    "headline": {"x":80,"y":80,"max_width":920,"font_size":72,"font_weight":700,"color":"#FFFFFF","align":"left"},
    "logo":     {"x":880,"y":880,"size":160}
  }
  $$::jsonb,
  '{"text_color_fallback":"#FFFFFF","logo_position":"bottom-right"}'::jsonb
),
(
  'Story Vertical', 'story',
  '{"width":1080,"height":1920}'::jsonb,
  $$
  {
    "headline": {"x":80,"y":400,"max_width":920,"font_size":80,"font_weight":700,"color":"#FFFFFF","align":"center"},
    "logo":     {"x":480,"y":1700,"size":120}
  }
  $$::jsonb,
  '{"text_color_fallback":"#FFFFFF","logo_position":"bottom-center"}'::jsonb
),
(
  'Carrossel Capa', 'carousel_slide',
  '{"width":1080,"height":1080}'::jsonb,
  $$
  {
    "headline":        {"x":80,"y":80,"max_width":920,"font_size":80,"font_weight":700,"color":"#FFFFFF","align":"left"},
    "page_indicator":  {"x":1000,"y":80,"text":"1/N"},
    "logo":            {"x":880,"y":880,"size":160}
  }
  $$::jsonb,
  '{"text_color_fallback":"#FFFFFF"}'::jsonb
),
(
  'Carrossel Conteúdo', 'carousel_slide',
  '{"width":1080,"height":1080}'::jsonb,
  $$
  {
    "headline":       {"x":80,"y":80,"max_width":920,"font_size":56,"font_weight":600,"color":"#FFFFFF","align":"left"},
    "body":           {"x":80,"y":220,"max_width":920,"font_size":36,"color":"#FFFFFF"},
    "page_indicator": {"x":1000,"y":80}
  }
  $$::jsonb,
  '{"text_color_fallback":"#FFFFFF"}'::jsonb
),
(
  'Post Minimalista', 'post',
  '{"width":1080,"height":1080}'::jsonb,
  $$
  {
    "headline": {"x":80,"y":480,"max_width":920,"font_size":64,"font_weight":700,"color":"#080808","align":"center"},
    "logo":     {"x":480,"y":880,"size":120}
  }
  $$::jsonb,
  '{"text_color_fallback":"#080808","background_overlay":"rgba(255,255,255,0.85)"}'::jsonb
)
ON CONFLICT DO NOTHING;

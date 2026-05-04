"""
Teste: Gera carousel de 5 slides para OrbitaIA.
Uso: cd apps/backend && python test_orbitaia_carousel.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Garante imports do projeto
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.engines.image_engine.imagen_client import generate_carousel_images
from src.engines.image_engine.composer import compose_branded_slide
from src.engines.script_engine.templates.library import get_template_by_id


OUTPUT_DIR = Path("/tmp/uploads/orbitaia_carousel")

# Brand context da OrbitaIA
BRAND_CONTEXT = {
    "visual_identity": {
        "primary_color": "#1a1a2e",
        "secondary_color": "#0f3460",
        "accent_color": "#FF6B35",
        "style_description": "Dark cosmic tech aesthetic, premium, futuristic, orange accents on deep navy/black backgrounds",
    },
}


async def main():
    template = get_template_by_id("tech-consultoria-dor-solucao")
    if not template:
        print("Template 'tech-consultoria-dor-solucao' nao encontrado!")
        return

    slide_prompts = template["visual_hint_slides"]
    slide_texts = template["slide_texts_pt"]

    print(f"Gerando {len(slide_prompts)} imagens via Imagen 4.0...")
    images = await generate_carousel_images(slide_prompts, "post", BRAND_CONTEXT)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, (img_bytes, text_data) in enumerate(zip(images, slide_texts)):
        if img_bytes is None:
            print(f"  Slide {i+1}: FALHOU na geracao de imagem")
            continue

        print(f"  Slide {i+1}: imagem gerada ({len(img_bytes)} bytes), aplicando texto...")

        # Aplica overlay com texto em PT e destaques em laranja
        final = compose_branded_slide(
            image_bytes=img_bytes,
            text=text_data["main"],
            highlights=text_data.get("highlights"),
            accent_color="#FF6B35",
            text_color="#FFFFFF",
            overlay_color="#0a0e27",
            overlay_opacity=160,
            font_name="poppins-bold",
            font_size=58,
            position="center",
        )

        out_path = OUTPUT_DIR / f"slide_{i+1}.jpg"
        out_path.write_bytes(final)
        print(f"  Slide {i+1}: salvo em {out_path} ({len(final)} bytes)")

    print(f"\nCarousel completo! Arquivos em: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())

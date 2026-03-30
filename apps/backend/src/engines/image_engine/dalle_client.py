import os
import logging
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

IMAGE_FORMATS = {
    "post": {"size": "1024x1024", "ratio": "1:1"},
    "story": {"size": "1024x1792", "ratio": "9:16"},
    "landscape": {"size": "1792x1024", "ratio": "1.91:1"},
}

IMAGE_SYSTEM = (
    "Professional marketing photo for Brazilian business. "
    "High quality, clean, modern aesthetic. "
    "No text overlays in the image. "
    "Style: commercial photography, well-lit, sharp."
)


async def generate_image(visual_description: str, format: str = "post", brand_context: dict | None = None) -> bytes:
    """Gera imagem via DALL-E 3 HD e retorna os bytes."""
    fmt = IMAGE_FORMATS.get(format, IMAGE_FORMATS["post"])

    # Build prompt with brand context
    from src.engines.image_engine.imagen_client import build_image_prompt
    full_prompt = build_image_prompt(visual_description, format, brand_context)

    try:
        response = await client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size=fmt["size"],
            quality="hd",
            n=1,
            response_format="url",
        )
        image_url = response.data[0].url
        async with httpx.AsyncClient() as http:
            r = await http.get(image_url, timeout=60)
            r.raise_for_status()
            return r.content
    except Exception as e:
        logger.error({"event": "dalle_error", "error": str(e)})
        raise

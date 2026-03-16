import os
import logging
import asyncio

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

MODEL = "gemini-3.1-flash-image-preview"

IMAGE_PREFIX = (
    "Professional marketing photo for Brazilian business, "
    "high quality, clean modern aesthetic, no text overlays, "
    "commercial photography, well-lit, sharp. "
)


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não configurada no .env")
        _client = genai.Client(api_key=api_key)
    return _client


async def generate_image_gemini(visual_description: str, format: str = "post") -> bytes:
    """Gera imagem via gemini-2.0-flash-preview-image-generation e retorna bytes."""
    prompt = IMAGE_PREFIX + visual_description

    logger.info({"event": "gemini_image_request", "model": MODEL, "format": format})

    def _generate() -> bytes:
        client = _get_client()
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return part.inline_data.data
        raise ValueError(f"{MODEL}: nenhuma imagem na resposta")

    image_bytes = await asyncio.to_thread(_generate)
    logger.info({"event": "gemini_image_done", "bytes": len(image_bytes)})
    return image_bytes

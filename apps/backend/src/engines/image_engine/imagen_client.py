"""
Image Generation — Gemini 3.1 Flash com prompts profissionais e brand context.
"""
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


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não configurada no .env")
        _client = genai.Client(api_key=api_key)
    return _client


def build_image_prompt(
    visual_description: str,
    format: str = "post",
    brand_context: dict | None = None,
) -> str:
    """Constrói prompt profissional com brand context."""
    parts = [visual_description.strip()]

    if brand_context:
        vi = brand_context.get("visual_identity", {})
        colors = []
        if vi.get("primary_color"):
            colors.append(vi["primary_color"])
        if vi.get("secondary_color"):
            colors.append(vi["secondary_color"])
        if vi.get("accent_color"):
            colors.append(vi["accent_color"])
        if colors:
            parts.append(f"Color palette: {', '.join(colors)}.")
        if vi.get("style_description"):
            parts.append(f"Brand style: {vi['style_description']}.")

    desc_lower = visual_description.lower()
    if "8k" not in desc_lower and "high resolution" not in desc_lower:
        parts.append("8K resolution, ultra-detailed, professional color grading.")
    if "no text" not in desc_lower:
        parts.append("No text, no watermarks, no logos, no graphic overlays.")
    if "photorealistic" not in desc_lower and "photograph" not in desc_lower:
        parts.append("Photorealistic, commercial advertising quality.")

    return " ".join(parts)


async def generate_image_gemini(
    visual_description: str,
    format: str = "post",
    brand_context: dict | None = None,
) -> bytes:
    """Gera imagem via Gemini 3.1 Flash. Retorna bytes."""
    prompt = build_image_prompt(visual_description, format, brand_context)

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

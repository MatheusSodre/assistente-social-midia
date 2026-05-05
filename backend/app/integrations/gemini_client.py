import io
import time

from google import genai
from google.genai import types
from PIL import Image

from app.integrations.image_provider import ImageResult


class GeminiImageProvider:
    """
    Gemini Flash Image (Nano Banana 2). O modelo não aceita dimensões como
    parâmetro estruturado — incluímos a proporção/dimensões no prompt e
    redimensionamos com Pillow se o output divergir.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate(
        self,
        *,
        prompt: str,
        width: int,
        height: int,
        seed: int | None = None,
    ) -> ImageResult:
        start = time.monotonic()

        ratio = self._aspect_ratio(width, height)
        full_prompt = (
            f"{prompt}\n\n"
            f"Output format: photographic image, {width}x{height} pixels, "
            f"aspect ratio {ratio}. No text, no captions, no watermarks."
        )

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        png_bytes = self._extract_png(response)
        png_bytes = self._ensure_dimensions(png_bytes, width, height)

        latency_ms = int((time.monotonic() - start) * 1000)
        return ImageResult(
            png_bytes=png_bytes,
            model=self._model,
            latency_ms=latency_ms,
            metadata={"prompt_chars": len(full_prompt)},
        )

    @staticmethod
    def _extract_png(response) -> bytes:
        for candidate in response.candidates or []:
            for part in (candidate.content.parts if candidate.content else []) or []:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None):
                    return inline.data
        raise RuntimeError("Gemini não retornou imagem inline_data")

    @staticmethod
    def _ensure_dimensions(png_bytes: bytes, width: int, height: int) -> bytes:
        with Image.open(io.BytesIO(png_bytes)) as img:
            if img.size == (width, height):
                return png_bytes
            resized = img.convert("RGB").resize((width, height), Image.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format="PNG", optimize=True)
            return buf.getvalue()

    @staticmethod
    def _aspect_ratio(width: int, height: int) -> str:
        from math import gcd
        g = gcd(width, height)
        return f"{width // g}:{height // g}"

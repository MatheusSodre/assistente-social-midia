"""
Video Composer — Orquestra geração de vídeo: imagem → Runway → narração → merge.
"""
import logging
import uuid
from pathlib import Path
from typing import Any

from src.engines.image_engine.storage import upload_image, save_image_locally

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("/home/sodre/www/orbita.ia/assistente-social-midia/apps/backend/uploads")


async def compose_reel(
    image_bytes: bytes,
    video_prompt: str,
    narration_text: str | None = None,
    duration: int = 5,
) -> dict[str, Any]:
    """
    Pipeline completo de criação de Reel:
    1. Upload da imagem base
    2. Gera vídeo via Runway (image-to-video)
    3. Opcionalmente adiciona narração via ElevenLabs
    4. Retorna URLs do vídeo e imagem thumbnail
    """
    from .runway_client import generate_video_from_image
    from .tts_client import generate_narration

    # 1. Upload imagem como thumbnail e para Runway
    image_url = save_image_locally(image_bytes, "reel", "jpg")
    # Runway precisa de URL pública — em dev, usamos placeholder
    full_image_url = f"http://localhost:8000{image_url}"

    # 2. Gera vídeo via Runway
    video_bytes = await generate_video_from_image(
        image_url=full_image_url,
        prompt=video_prompt,
        duration=duration,
    )

    video_url = None
    if video_bytes:
        # Salvar vídeo localmente
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        video_filename = f"{uuid.uuid4()}.mp4"
        video_path = UPLOAD_DIR / video_filename
        video_path.write_bytes(video_bytes)
        video_url = f"/uploads/{video_filename}"
        logger.info({"event": "reel_video_saved", "url": video_url})

    # 3. Narração (opcional)
    narration_url = None
    if narration_text:
        audio_bytes = await generate_narration(narration_text)
        if audio_bytes:
            audio_filename = f"{uuid.uuid4()}.mp3"
            audio_path = UPLOAD_DIR / audio_filename
            audio_path.write_bytes(audio_bytes)
            narration_url = f"/uploads/{audio_filename}"

    return {
        "image_url": image_url,
        "video_url": video_url,
        "narration_url": narration_url,
        "duration": duration,
        "has_video": video_url is not None,
    }

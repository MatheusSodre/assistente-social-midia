"""
ElevenLabs TTS Client — Gera narração em português para vídeos.
"""
import os
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah - natural female voice


async def generate_narration(
    text: str,
    voice_id: str = DEFAULT_VOICE_ID,
) -> bytes | None:
    """Gera áudio de narração via ElevenLabs TTS. Retorna bytes MP3 ou None."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        logger.warning("ELEVENLABS_API_KEY nao configurada — video sem narracao")
        return None

    async with httpx.AsyncClient(timeout=30) as http:
        r = await http.post(
            f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.3,
                },
            },
        )
        r.raise_for_status()
        logger.info({"event": "tts_done", "bytes": len(r.content)})
        return r.content

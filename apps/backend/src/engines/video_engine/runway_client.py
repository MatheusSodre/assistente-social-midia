"""
Runway ML Client — Gera vídeos curtos a partir de imagem + prompt.
Usado para criar Reels no Instagram.
"""
import os
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)

RUNWAY_API_BASE = "https://api.dev.runwayml.com/v1"


async def generate_video_from_image(
    image_url: str,
    prompt: str,
    duration: int = 5,
) -> bytes | None:
    """
    Gera vídeo via Runway Gen-3 Alpha a partir de imagem + prompt.
    Retorna bytes do vídeo ou None se falhar.
    """
    api_key = os.getenv("RUNWAY_API_KEY", "")
    if not api_key:
        logger.warning("RUNWAY_API_KEY nao configurada — usando fallback de video")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Runway-Version": "2024-11-06",
    }

    async with httpx.AsyncClient(timeout=120) as http:
        # 1. Criar task de geração
        r = await http.post(
            f"{RUNWAY_API_BASE}/image_to_video",
            headers=headers,
            json={
                "model": "gen3a_turbo",
                "promptImage": image_url,
                "promptText": prompt,
                "duration": duration,
                "ratio": "9:16",  # vertical para Reels
                "watermark": False,
            },
        )
        r.raise_for_status()
        task_id = r.json().get("id")
        logger.info({"event": "runway_task_created", "task_id": task_id})

        # 2. Poll até completar
        for _ in range(60):  # max 5 min
            await asyncio.sleep(5)
            r2 = await http.get(
                f"{RUNWAY_API_BASE}/tasks/{task_id}",
                headers=headers,
            )
            r2.raise_for_status()
            status = r2.json().get("status")
            if status == "SUCCEEDED":
                output_url = r2.json().get("output", [None])[0]
                if output_url:
                    # Download video
                    r3 = await http.get(output_url, timeout=60)
                    r3.raise_for_status()
                    logger.info({"event": "runway_video_done", "task_id": task_id, "bytes": len(r3.content)})
                    return r3.content
                return None
            elif status == "FAILED":
                logger.error({"event": "runway_video_failed", "task_id": task_id, "detail": r2.json()})
                return None

    logger.error({"event": "runway_video_timeout", "task_id": task_id})
    return None

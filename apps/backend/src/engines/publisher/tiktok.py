"""
TikTok Publisher — Publica vídeos no TikTok via Content Posting API.
Docs: https://developers.tiktok.com/doc/content-posting-api-get-started
"""
import os
import logging
import asyncio

import httpx

logger = logging.getLogger(__name__)

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"


async def publish_video(
    access_token: str,
    video_url: str,
    caption: str,
) -> str:
    """Publica vídeo no TikTok. Retorna publish_id."""
    async with httpx.AsyncClient(timeout=120) as http:
        # 1. Init upload
        r = await http.post(
            f"{TIKTOK_API_BASE}/post/publish/video/init/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "post_info": {
                    "title": caption[:150],
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "video_url": video_url,
                },
            },
        )
        r.raise_for_status()
        publish_id = r.json().get("data", {}).get("publish_id")
        logger.info({"event": "tiktok_publish_initiated", "publish_id": publish_id})

        # 2. Poll status
        for _ in range(30):
            await asyncio.sleep(5)
            r2 = await http.post(
                f"{TIKTOK_API_BASE}/post/publish/status/fetch/",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={"publish_id": publish_id},
            )
            status = r2.json().get("data", {}).get("status")
            if status == "PUBLISH_COMPLETE":
                logger.info({"event": "tiktok_published", "publish_id": publish_id})
                return publish_id
            elif status in ("FAILED", "PUBLISH_FAILED"):
                raise ValueError(f"TikTok publish failed: {r2.json()}")

        raise TimeoutError("TikTok publish timeout")

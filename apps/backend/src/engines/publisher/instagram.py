import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


async def publish_image_post(
    instagram_account_id: str,
    access_token: str,
    image_url: str,
    caption: str,
) -> str:
    """Publica um post de imagem no Instagram. Retorna instagram_media_id."""
    async with httpx.AsyncClient(timeout=60) as http:
        # 1. Cria container de mídia
        r = await http.post(
            f"{GRAPH_API_BASE}/{instagram_account_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": access_token,
            },
        )
        r.raise_for_status()
        creation_id = r.json()["id"]
        logger.info({"event": "ig_media_container_created", "creation_id": creation_id})

        # 2. Publica o container
        r2 = await http.post(
            f"{GRAPH_API_BASE}/{instagram_account_id}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": access_token,
            },
        )
        r2.raise_for_status()
        media_id = r2.json()["id"]
        logger.info({"event": "ig_post_published", "media_id": media_id})
        return media_id

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


async def publish_carousel_post(
    instagram_account_id: str,
    access_token: str,
    image_urls: list[str],
    caption: str,
) -> str:
    """Publica um carrossel (2-10 imagens) no Instagram. Retorna instagram_media_id."""
    if len(image_urls) < 2:
        raise ValueError("Carrossel precisa de no mínimo 2 imagens")
    if len(image_urls) > 10:
        raise ValueError("Carrossel suporta no máximo 10 imagens")

    async with httpx.AsyncClient(timeout=60) as http:
        # 1. Cria container individual para cada imagem
        children_ids = []
        for url in image_urls:
            r = await http.post(
                f"{GRAPH_API_BASE}/{instagram_account_id}/media",
                data={
                    "image_url": url,
                    "is_carousel_item": "true",
                    "access_token": access_token,
                },
            )
            r.raise_for_status()
            children_ids.append(r.json()["id"])
            logger.info({"event": "ig_carousel_item_created", "creation_id": r.json()["id"]})

        # 2. Cria container do carrossel
        r2 = await http.post(
            f"{GRAPH_API_BASE}/{instagram_account_id}/media",
            data={
                "media_type": "CAROUSEL",
                "caption": caption,
                "children": ",".join(children_ids),
                "access_token": access_token,
            },
        )
        r2.raise_for_status()
        carousel_id = r2.json()["id"]
        logger.info({"event": "ig_carousel_container_created", "carousel_id": carousel_id})

        # 3. Publica o carrossel
        r3 = await http.post(
            f"{GRAPH_API_BASE}/{instagram_account_id}/media_publish",
            data={
                "creation_id": carousel_id,
                "access_token": access_token,
            },
        )
        r3.raise_for_status()
        media_id = r3.json()["id"]
        logger.info({"event": "ig_carousel_published", "media_id": media_id})
        return media_id


async def publish_reel(
    instagram_account_id: str,
    access_token: str,
    video_url: str,
    caption: str,
) -> str:
    """Publica um Reel no Instagram. Retorna instagram_media_id."""
    async with httpx.AsyncClient(timeout=120) as http:
        # 1. Cria container de vídeo
        r = await http.post(
            f"{GRAPH_API_BASE}/{instagram_account_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": access_token,
            },
        )
        r.raise_for_status()
        creation_id = r.json()["id"]
        logger.info({"event": "ig_reel_container_created", "creation_id": creation_id})

        # 2. Poll status até estar pronto (vídeo precisa ser processado)
        import asyncio
        for _ in range(30):
            await asyncio.sleep(5)
            r_status = await http.get(
                f"{GRAPH_API_BASE}/{creation_id}",
                params={"fields": "status_code", "access_token": access_token},
            )
            status = r_status.json().get("status_code")
            if status == "FINISHED":
                break
            elif status == "ERROR":
                raise ValueError(f"Reel processing failed: {r_status.json()}")

        # 3. Publica o container
        r2 = await http.post(
            f"{GRAPH_API_BASE}/{instagram_account_id}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": access_token,
            },
        )
        r2.raise_for_status()
        media_id = r2.json()["id"]
        logger.info({"event": "ig_reel_published", "media_id": media_id})
        return media_id


async def fetch_recent_posts(
    instagram_account_id: str,
    access_token: str,
    limit: int = 12,
) -> list[dict]:
    """Busca os posts recentes via Graph API. Retorna lista de posts com caption, tipo, timestamp e media_url."""
    async with httpx.AsyncClient(timeout=30) as http:
        r = await http.get(
            f"{GRAPH_API_BASE}/{instagram_account_id}/media",
            params={
                "fields": "id,caption,media_type,media_url,thumbnail_url,timestamp,permalink",
                "limit": limit,
                "access_token": access_token,
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("data", [])

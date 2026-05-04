"""
LinkedIn Publisher — Publica posts no LinkedIn via API.
Docs: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/
"""
import logging

import httpx

logger = logging.getLogger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"


async def publish_image_post(
    person_urn: str,
    access_token: str,
    image_url: str,
    text: str,
) -> str:
    """Publica post com imagem no LinkedIn. Retorna post ID."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    async with httpx.AsyncClient(timeout=60) as http:
        # 1. Register image upload
        r = await http.post(
            f"{LINKEDIN_API_BASE}/assets?action=registerUpload",
            headers=headers,
            json={
                "registerUploadRequest": {
                    "owner": person_urn,
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "serviceRelationships": [
                        {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                    ],
                }
            },
        )
        r.raise_for_status()
        upload_url = r.json()["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
        asset = r.json()["value"]["asset"]

        # 2. Upload image
        img_resp = await http.get(image_url, timeout=30)
        await http.put(upload_url, headers={"Authorization": f"Bearer {access_token}"}, content=img_resp.content)

        # 3. Create post
        r2 = await http.post(
            f"{LINKEDIN_API_BASE}/ugcPosts",
            headers=headers,
            json={
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "IMAGE",
                        "media": [{
                            "status": "READY",
                            "media": asset,
                        }],
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            },
        )
        r2.raise_for_status()
        post_id = r2.headers.get("x-restli-id", r2.json().get("id", ""))
        logger.info({"event": "linkedin_published", "post_id": post_id})
        return post_id


async def publish_text_post(
    person_urn: str,
    access_token: str,
    text: str,
) -> str:
    """Publica post de texto no LinkedIn."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    async with httpx.AsyncClient(timeout=30) as http:
        r = await http.post(
            f"{LINKEDIN_API_BASE}/ugcPosts",
            headers=headers,
            json={
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            },
        )
        r.raise_for_status()
        post_id = r.headers.get("x-restli-id", r.json().get("id", ""))
        logger.info({"event": "linkedin_text_published", "post_id": post_id})
        return post_id

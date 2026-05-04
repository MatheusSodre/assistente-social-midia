"""
Instagram Metrics — Busca métricas de engajamento dos posts publicados via Graph API.
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


async def fetch_post_insights(
    media_id: str,
    access_token: str,
) -> dict[str, Any]:
    """Busca métricas de um post específico via Graph API."""
    async with httpx.AsyncClient(timeout=15) as http:
        # Basic metrics (likes, comments)
        r = await http.get(
            f"{GRAPH_API_BASE}/{media_id}",
            params={
                "fields": "like_count,comments_count,timestamp,media_type",
                "access_token": access_token,
            },
        )
        r.raise_for_status()
        data = r.json()

        # Insights (reach, impressions) — requer permissão instagram_manage_insights
        insights = {}
        try:
            r2 = await http.get(
                f"{GRAPH_API_BASE}/{media_id}/insights",
                params={
                    "metric": "reach,impressions,saved,shares",
                    "access_token": access_token,
                },
            )
            if r2.status_code == 200:
                for item in r2.json().get("data", []):
                    insights[item["name"]] = item["values"][0]["value"] if item.get("values") else 0
        except Exception as e:
            logger.warning({"event": "ig_insights_partial", "media_id": media_id, "error": str(e)})

        likes = data.get("like_count", 0)
        comments = data.get("comments_count", 0)
        reach = insights.get("reach", 0)
        impressions = insights.get("impressions", 0)
        saved = insights.get("saved", 0)
        shares = insights.get("shares", 0)

        engagement_rate = 0.0
        if reach > 0:
            engagement_rate = round(((likes + comments + saved + shares) / reach) * 100, 2)

        return {
            "media_id": media_id,
            "likes": likes,
            "comments": comments,
            "reach": reach,
            "impressions": impressions,
            "saved": saved,
            "shares": shares,
            "engagement_rate": engagement_rate,
            "media_type": data.get("media_type"),
        }


async def fetch_account_insights(
    instagram_account_id: str,
    access_token: str,
) -> dict[str, Any]:
    """Busca métricas gerais da conta (followers, reach, impressions)."""
    async with httpx.AsyncClient(timeout=15) as http:
        # Follower count
        r = await http.get(
            f"{GRAPH_API_BASE}/{instagram_account_id}",
            params={
                "fields": "followers_count,media_count,username",
                "access_token": access_token,
            },
        )
        r.raise_for_status()
        account = r.json()

        # Account insights (últimos 30 dias)
        account_insights = {}
        try:
            r2 = await http.get(
                f"{GRAPH_API_BASE}/{instagram_account_id}/insights",
                params={
                    "metric": "reach,impressions,follower_count",
                    "period": "day",
                    "since": "",  # last 30 days default
                    "access_token": access_token,
                },
            )
            if r2.status_code == 200:
                for item in r2.json().get("data", []):
                    total = sum(v["value"] for v in item.get("values", []) if isinstance(v.get("value"), (int, float)))
                    account_insights[item["name"]] = total
        except Exception as e:
            logger.warning({"event": "ig_account_insights_partial", "error": str(e)})

        return {
            "username": account.get("username", ""),
            "followers_count": account.get("followers_count", 0),
            "media_count": account.get("media_count", 0),
            "reach_30d": account_insights.get("reach", 0),
            "impressions_30d": account_insights.get("impressions", 0),
        }

import json
from typing import Any

from fastapi import APIRouter, Depends, Query

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


@router.get("/analytics")
def analytics(
    business_id: str = Query(...),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    # Verify ownership
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, user["sub"]),
            )
            if not cur.fetchone():
                from fastapi import HTTPException
                raise HTTPException(404, "Business não encontrado")

            cur.execute(
                """SELECT
                     COUNT(*) as total_drafts,
                     SUM(CASE WHEN status IN ('approved','published') THEN 1 ELSE 0 END) as approved,
                     SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                     SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published
                   FROM content_drafts WHERE business_id = %s""",
                (business_id,),
            )
            totals = cur.fetchone() or {}

            cur.execute(
                """SELECT format, COUNT(*) as cnt FROM content_drafts
                   WHERE business_id = %s AND status IN ('approved','published')
                   GROUP BY format ORDER BY cnt DESC""",
                (business_id,),
            )
            by_format = cur.fetchall() or []

            cur.execute(
                """SELECT best_posting_time, COUNT(*) as cnt FROM content_drafts
                   WHERE business_id = %s AND best_posting_time IS NOT NULL
                   GROUP BY best_posting_time ORDER BY cnt DESC LIMIT 5""",
                (business_id,),
            )
            best_times = cur.fetchall() or []

            cur.execute(
                """SELECT DATE(criado_em) as day, COUNT(*) as cnt
                   FROM content_drafts
                   WHERE business_id = %s AND criado_em >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                   GROUP BY day ORDER BY day""",
                (business_id,),
            )
            trend = cur.fetchall() or []

    total = totals.get("total_drafts") or 0
    approved = totals.get("approved") or 0
    approval_rate = round((approved / total * 100) if total > 0 else 0, 1)

    return {
        "business_id": business_id,
        "total_drafts": total,
        "approved": approved,
        "rejected": totals.get("rejected") or 0,
        "published": totals.get("published") or 0,
        "approval_rate_pct": approval_rate,
        "top_formats": [{"format": r["format"], "count": r["cnt"]} for r in by_format],
        "best_times": [{"time": r["best_posting_time"], "count": r["cnt"]} for r in best_times],
        "trend_30d": [{"day": str(r["day"]), "count": r["cnt"]} for r in trend],
    }


@router.post("/sync-metrics")
async def sync_metrics(business_id: str = Query(...), user=Depends(get_current_user)) -> dict[str, Any]:
    """Busca métricas reais dos posts publicados via Instagram Graph API."""
    from src.engines.intelligence.ig_metrics import fetch_post_insights
    from src.engines.publisher.token_manager import decrypt_token
    from datetime import datetime

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT instagram_account_id, instagram_access_token FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, user["sub"]),
            )
            biz = cur.fetchone()

    if not biz or not biz.get("instagram_access_token"):
        from fastapi import HTTPException
        raise HTTPException(400, "Instagram nao conectado")

    access_token = decrypt_token(biz["instagram_access_token"])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT sp.id, sp.instagram_media_id
                   FROM scheduled_posts sp
                   JOIN content_drafts cd ON cd.id = sp.content_draft_id
                   WHERE cd.business_id = %s AND sp.status = 'published'
                     AND sp.instagram_media_id IS NOT NULL
                   ORDER BY sp.posted_at DESC LIMIT 20""",
                (business_id,),
            )
            posts = cur.fetchall() or []

    updated = 0
    errors = 0
    for post in posts:
        try:
            metrics = await fetch_post_insights(post["instagram_media_id"], access_token)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE scheduled_posts SET
                           likes = %s, comments = %s, reach = %s, impressions = %s,
                           saved = %s, shares = %s, engagement_rate = %s,
                           metrics_updated_at = %s
                           WHERE id = %s""",
                        (
                            metrics["likes"], metrics["comments"], metrics["reach"],
                            metrics["impressions"], metrics["saved"], metrics["shares"],
                            metrics["engagement_rate"], datetime.utcnow(), post["id"],
                        ),
                    )
            updated += 1
        except Exception:
            errors += 1

    return {"synced": updated, "errors": errors, "total": len(posts)}


@router.get("/history")
def history(user=Depends(get_current_user), limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sp.id, sp.platform, sp.scheduled_for, sp.posted_at,
                       sp.instagram_media_id, sp.status,
                       sp.likes, sp.comments, sp.reach, sp.impressions,
                       sp.saved, sp.shares, sp.engagement_rate,
                       cd.format, cd.caption, cd.image_url,
                       b.name as business_name, b.id as business_id
                FROM scheduled_posts sp
                JOIN content_drafts cd ON cd.id = sp.content_draft_id
                JOIN businesses b ON b.id = cd.business_id
                WHERE b.usuario_id = %s AND sp.status = 'published'
                ORDER BY sp.posted_at DESC
                LIMIT %s
                """,
                (user["sub"], limit),
            )
            rows = cur.fetchall()
    return rows or []

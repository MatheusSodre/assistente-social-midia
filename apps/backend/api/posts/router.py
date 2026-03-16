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


@router.get("/history")
def history(user=Depends(get_current_user), limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sp.id, sp.platform, sp.scheduled_for, sp.posted_at,
                       sp.instagram_media_id, sp.status,
                       cd.format, cd.caption, cd.image_url,
                       b.name as business_name
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

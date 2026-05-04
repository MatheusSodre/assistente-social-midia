from pydantic import BaseModel
from typing import Optional


class SubscriptionResponse(BaseModel):
    plano: str
    status: str
    posts_used: int
    posts_limit: int
    businesses_limit: int
    instagram_limit: int
    trial_ends_at: Optional[str] = None
    current_period_end: Optional[str] = None


# Limites por plano
PLAN_LIMITS = {
    "starter": {
        "posts_per_month": 15,
        "formats": ["post", "story"],
        "businesses": 1,
        "instagram_accounts": 1,
        "agents": ["sofia"],
        "ig_style_analysis": False,
    },
    "pro": {
        "posts_per_month": 50,
        "formats": ["post", "story", "reel", "carrossel"],
        "businesses": 3,
        "instagram_accounts": 3,
        "agents": ["sofia", "mara", "pixel"],
        "ig_style_analysis": True,
    },
    "premium": {
        "posts_per_month": 999999,  # ilimitado
        "formats": ["post", "story", "reel", "carrossel"],
        "businesses": 10,
        "instagram_accounts": 10,
        "agents": ["sofia", "mara", "pixel", "luna"],
        "ig_style_analysis": True,
    },
}

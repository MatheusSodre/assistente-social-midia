"""
Google Ads API client wrapper.
Uses per-business credentials stored in DB (encrypted).
Falls back to mock data when credentials are not configured.
"""
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Global env credentials (used as fallback / default developer token)
DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")


def _decrypt_token(encrypted: str) -> str:
    """Decrypt a Fernet-encrypted token."""
    try:
        from cryptography.fernet import Fernet
        key = os.getenv("ENCRYPTION_KEY", "")
        if not key:
            return encrypted  # dev fallback: assume plain text
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.decrypt(encrypted.encode()).decode()
    except Exception:
        return encrypted


def _encrypt_token(plain: str) -> str:
    """Encrypt a token with Fernet."""
    try:
        from cryptography.fernet import Fernet
        key = os.getenv("ENCRYPTION_KEY", "")
        if not key:
            return plain
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.encrypt(plain.encode()).decode()
    except Exception:
        return plain


def build_client(refresh_token: str, customer_id: str, login_customer_id: str | None = None):
    """Build a GoogleAdsClient for a specific business account."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
        config = {
            "developer_token": DEVELOPER_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": _decrypt_token(refresh_token),
            "use_proto_plus": True,
        }
        if login_customer_id:
            config["login_customer_id"] = login_customer_id
        return GoogleAdsClient.load_from_dict(config)
    except ImportError:
        raise RuntimeError("google-ads não instalado. Rode: pip install google-ads")


def get_campaigns(client, customer_id: str) -> list[dict[str, Any]]:
    """List all campaigns with basic metrics."""
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign_budget.amount_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.ctr,
            metrics.average_cpc,
            metrics.conversions
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY metrics.cost_micros DESC
        LIMIT 20
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    campaigns = []
    for row in response:
        campaigns.append({
            "id": str(row.campaign.id),
            "name": row.campaign.name,
            "status": row.campaign.status.name,
            "channel": row.campaign.advertising_channel_type.name,
            "budget_daily_brl": round(row.campaign_budget.amount_micros / 1_000_000, 2),
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost_brl": round(row.metrics.cost_micros / 1_000_000, 2),
            "ctr_pct": round(row.metrics.ctr * 100, 2),
            "avg_cpc_brl": round(row.metrics.average_cpc / 1_000_000, 2),
            "conversions": round(row.metrics.conversions, 1),
        })
    return campaigns


def get_account_overview(client, customer_id: str) -> dict[str, Any]:
    """Get account-level metrics for last 30 days."""
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.ctr,
            metrics.conversions,
            metrics.average_cpc
        FROM customer
        WHERE segments.date DURING LAST_30_DAYS
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    totals = {"impressions": 0, "clicks": 0, "cost_micros": 0, "conversions": 0.0}
    for row in response:
        totals["impressions"] += row.metrics.impressions
        totals["clicks"] += row.metrics.clicks
        totals["cost_micros"] += row.metrics.cost_micros
        totals["conversions"] += row.metrics.conversions

    total_cost = totals["cost_micros"] / 1_000_000
    ctr = (totals["clicks"] / totals["impressions"] * 100) if totals["impressions"] > 0 else 0
    avg_cpc = (total_cost / totals["clicks"]) if totals["clicks"] > 0 else 0

    return {
        "impressions": totals["impressions"],
        "clicks": totals["clicks"],
        "cost_brl": round(total_cost, 2),
        "ctr_pct": round(ctr, 2),
        "avg_cpc_brl": round(avg_cpc, 2),
        "conversions": round(totals["conversions"], 1),
        "cost_per_conversion_brl": round(total_cost / totals["conversions"], 2) if totals["conversions"] > 0 else 0,
    }


def pause_campaign(client, customer_id: str, campaign_id: str) -> dict[str, Any]:
    """Pause a campaign."""
    from google.ads.googleads.errors import GoogleAdsException
    campaign_service = client.get_service("CampaignService")
    campaign_op = client.get_type("CampaignOperation")
    campaign = campaign_op.update
    campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
    campaign.status = client.enums.CampaignStatusEnum.PAUSED
    client.copy_from(campaign_op.update_mask, protobuf_helpers.field_mask(None, campaign._pb))
    response = campaign_service.mutate_campaigns(customer_id=customer_id, operations=[campaign_op])
    return {"success": True, "campaign_id": campaign_id, "new_status": "PAUSED"}


def enable_campaign(client, customer_id: str, campaign_id: str) -> dict[str, Any]:
    """Enable a paused campaign."""
    campaign_service = client.get_service("CampaignService")
    campaign_op = client.get_type("CampaignOperation")
    campaign = campaign_op.update
    campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
    campaign.status = client.enums.CampaignStatusEnum.ENABLED
    from google.api_core import protobuf_helpers
    client.copy_from(campaign_op.update_mask, protobuf_helpers.field_mask(None, campaign._pb))
    response = campaign_service.mutate_campaigns(customer_id=customer_id, operations=[campaign_op])
    return {"success": True, "campaign_id": campaign_id, "new_status": "ENABLED"}


def get_keywords(client, customer_id: str, campaign_id: str | None = None) -> list[dict[str, Any]]:
    """Get keywords with performance metrics."""
    ga_service = client.get_service("GoogleAdsService")
    where_campaign = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.average_cpc,
            metrics.ctr
        FROM keyword_view
        WHERE segments.date DURING LAST_30_DAYS
            {where_campaign}
        ORDER BY metrics.cost_micros DESC
        LIMIT 50
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    keywords = []
    for row in response:
        keywords.append({
            "text": row.ad_group_criterion.keyword.text,
            "match_type": row.ad_group_criterion.keyword.match_type.name,
            "status": row.ad_group_criterion.status.name,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost_brl": round(row.metrics.cost_micros / 1_000_000, 2),
            "avg_cpc_brl": round(row.metrics.average_cpc / 1_000_000, 2),
            "ctr_pct": round(row.metrics.ctr * 100, 2),
        })
    return keywords


def update_campaign_budget(client, customer_id: str, campaign_budget_id: str, new_daily_budget_brl: float) -> dict[str, Any]:
    """Update the daily budget of a campaign budget."""
    budget_service = client.get_service("CampaignBudgetService")
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.update
    budget.resource_name = budget_service.campaign_budget_path(customer_id, campaign_budget_id)
    budget.amount_micros = int(new_daily_budget_brl * 1_000_000)
    from google.api_core import protobuf_helpers
    client.copy_from(budget_op.update_mask, protobuf_helpers.field_mask(None, budget._pb))
    budget_service.mutate_campaign_budgets(customer_id=customer_id, operations=[budget_op])
    return {"success": True, "new_daily_budget_brl": new_daily_budget_brl}


# ─── Mock data (when Google Ads not configured) ───────────────────────────────

MOCK_CAMPAIGNS = [
    {
        "id": "111111111",
        "name": "Campanha Search — Promoção Verão",
        "status": "ENABLED",
        "channel": "SEARCH",
        "budget_daily_brl": 50.0,
        "impressions": 12400,
        "clicks": 620,
        "cost_brl": 1240.0,
        "ctr_pct": 5.0,
        "avg_cpc_brl": 2.0,
        "conversions": 18.0,
    },
    {
        "id": "222222222",
        "name": "Campanha Display — Remarketing",
        "status": "PAUSED",
        "channel": "DISPLAY",
        "budget_daily_brl": 30.0,
        "impressions": 85000,
        "clicks": 340,
        "cost_brl": 510.0,
        "ctr_pct": 0.4,
        "avg_cpc_brl": 1.5,
        "conversions": 5.0,
    },
]

MOCK_OVERVIEW = {
    "impressions": 97400,
    "clicks": 960,
    "cost_brl": 1750.0,
    "ctr_pct": 0.99,
    "avg_cpc_brl": 1.82,
    "conversions": 23.0,
    "cost_per_conversion_brl": 76.09,
}

MOCK_KEYWORDS = [
    {"text": "clínica odontológica", "match_type": "BROAD", "status": "ENABLED", "impressions": 3200, "clicks": 160, "cost_brl": 320.0, "avg_cpc_brl": 2.0, "ctr_pct": 5.0},
    {"text": "dentista perto de mim", "match_type": "PHRASE", "status": "ENABLED", "impressions": 2800, "clicks": 196, "cost_brl": 392.0, "avg_cpc_brl": 2.0, "ctr_pct": 7.0},
    {"text": "limpeza dental preço", "match_type": "EXACT", "status": "ENABLED", "impressions": 1500, "clicks": 90, "cost_brl": 180.0, "avg_cpc_brl": 2.0, "ctr_pct": 6.0},
]

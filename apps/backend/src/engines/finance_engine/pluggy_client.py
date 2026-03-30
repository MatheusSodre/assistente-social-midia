import os
import time
import logging
from datetime import date, datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Cache da apiKey em memória { "key": str, "expires_at": float }
_api_key_cache: dict = {}
_CACHE_TTL = 90 * 60  # 90 minutos (apiKey válida por 2h)


class PluggyClient:
    BASE_URL = "https://api.pluggy.ai"

    def __init__(self) -> None:
        self.client_id = os.getenv("PLUGGY_CLIENT_ID", "")
        self.client_secret = os.getenv("PLUGGY_CLIENT_SECRET", "")
        self.static_api_key = os.getenv("PLUGGY_API_KEY", "")

    # ─── Auth ────────────────────────────────────────────────────────────────

    async def _get_api_key(self) -> str:
        # Se tiver API_KEY estática configurada, usa diretamente
        if self.static_api_key:
            return self.static_api_key

        now = time.monotonic()
        cached = _api_key_cache.get("key")
        if cached and _api_key_cache.get("expires_at", 0) > now:
            return cached

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/auth",
                json={"clientId": self.client_id, "clientSecret": self.client_secret},
                timeout=15,
            )
            resp.raise_for_status()
            api_key: str = resp.json()["apiKey"]

        _api_key_cache["key"] = api_key
        _api_key_cache["expires_at"] = now + _CACHE_TTL
        return api_key

    # ─── Connect Token ────────────────────────────────────────────────────────

    async def create_connect_token(self, user_id: str) -> str:
        api_key = await self._get_api_key()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/connect-token",
                json={"clientUserId": str(user_id)},
                headers={"X-API-KEY": api_key},
                timeout=15,
            )
            resp.raise_for_status()
        return resp.json()["accessToken"]

    # ─── Items ────────────────────────────────────────────────────────────────

    async def get_item(self, item_id: str) -> dict:
        api_key = await self._get_api_key()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/items/{item_id}",
                headers={"X-API-KEY": api_key},
                timeout=15,
            )
            resp.raise_for_status()
        return resp.json()

    # ─── Accounts ─────────────────────────────────────────────────────────────

    async def get_accounts(self, item_id: str) -> list[dict]:
        api_key = await self._get_api_key()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/accounts",
                params={"itemId": item_id},
                headers={"X-API-KEY": api_key},
                timeout=15,
            )
            resp.raise_for_status()
        return resp.json().get("results", [])

    # ─── Transactions ─────────────────────────────────────────────────────────

    async def get_transactions(
        self,
        account_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[dict]:
        api_key = await self._get_api_key()
        params: dict = {"accountId": account_id, "pageSize": 500}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()

        all_txs: list[dict] = []
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                params["page"] = page
                resp = await client.get(
                    f"{self.BASE_URL}/transactions",
                    params=params,
                    headers={"X-API-KEY": api_key},
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                all_txs.extend(results)
                if len(all_txs) >= data.get("total", 0):
                    break
                page += 1

        return all_txs

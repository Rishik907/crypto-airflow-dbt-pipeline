"""
Fetch task: pulls current daily price/market data for the fixed coin list
from CoinGecko's free /coins/markets endpoint (one call covers all coins).

Writes the fetched rows to XCom so the load task can pick them up without
re-hitting the API.
"""
import os
from datetime import datetime, timezone

import requests

from .coins import COINGECKO_IDS

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"


def fetch_daily_prices(**context):
    api_key = os.environ.get("COINGECKO_API_KEY")
    params = {
        "vs_currency": "usd",
        "ids": ",".join(COINGECKO_IDS),
        "price_change_percentage": "24h",
    }
    headers = {"x-cg-demo-api-key": api_key} if api_key else {}

    response = requests.get(
        f"{COINGECKO_BASE_URL}/coins/markets",
        params=params,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    raw_rows = response.json()

    fetched_at = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "coin_id": row["id"],
            "symbol": row["symbol"].upper(),
            "price_usd": row["current_price"],
            "market_cap_usd": row.get("market_cap"),
            "price_change_pct_24h": row.get("price_change_percentage_24h"),
            "fetched_at": fetched_at,
        }
        for row in raw_rows
    ]

    if len(rows) != len(COINGECKO_IDS):
        missing = set(COINGECKO_IDS) - {r["coin_id"] for r in rows}
        raise ValueError(f"CoinGecko response missing coins: {missing}")

    context["ti"].xcom_push(key="price_rows", value=rows)
    return len(rows)

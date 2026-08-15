# Fixed set of 10 coins for P3 (see project3-status.md decisions log).
# CoinGecko uses its own "id" slug, not the ticker, for API calls.
COINS = [
    {"id": "bitcoin", "symbol": "BTC"},
    {"id": "ethereum", "symbol": "ETH"},
    {"id": "ripple", "symbol": "XRP"},
    {"id": "binancecoin", "symbol": "BNB"},
    {"id": "solana", "symbol": "SOL"},
    {"id": "cardano", "symbol": "ADA"},
    {"id": "dogecoin", "symbol": "DOGE"},
    {"id": "tron", "symbol": "TRX"},
    {"id": "avalanche-2", "symbol": "AVAX"},
    {"id": "chainlink", "symbol": "LINK"},
]

COINGECKO_IDS = [c["id"] for c in COINS]

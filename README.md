# Crypto Market Analytics — Airflow + dbt + Snowflake

An orchestration-focused companion to a prior stock-analytics project. This
pipeline fetches daily crypto price snapshots from the CoinGecko API, loads
them into Snowflake, and transforms them into a small star schema using dbt —
all scheduled and orchestrated by Apache Airflow, running via Docker.

## What this project demonstrates

The prior project (`stock-market-dbt-pipeline`) proved the data modeling
approach works: yfinance → Snowflake → dbt (staging → intermediate → marts),
run manually via CLI. Orchestration was explicitly out of scope there.

This project fills that gap — the same modeling pattern, but with a
**different data source** (crypto instead of stocks, to keep the two projects
distinct) and a **scheduled, retried, monitored Airflow DAG** driving the
pipeline instead of one-off manual runs.

## Architecture

```
CoinGecko API  (/coins/markets, 10 coins)
      │
      ▼
Airflow task: fetch_prices               (pushes rows via XCom)
      │
      ▼
Airflow task: load_to_snowflake
      │  INSERT
      ▼
RAW.CRYPTO_PRICES_RAW                    (raw landing table, append-only)
      │
      ▼
┌──────────────────────────┐
│   dbt: staging layer     │   stg_crypto_prices
│  (dedup + surrogate key, │
│   incremental merge)     │
└──────────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ dbt: intermediate layer  │   int_crypto_daily_change
│  (day-over-day % change  │
│   via LAG)               │
└──────────────────────────┘
      │
      ▼
┌──────────────────────────┐
│    dbt: marts layer      │   dim_coin, dim_date, fct_crypto_price
└──────────────────────────┘
      │
      ▼
ANALYTICS schema — star schema, ready for querying

Airflow task: dbt deps && dbt run && dbt test
      (all three dbt layers run inside this single task,
       triggered daily on the crypto_pipeline_dag schedule)
```

**Airflow DAG (`crypto_pipeline_dag`)** — tagged `crypto`, `p3`, scheduled
daily at `30 0 * * *` UTC (06:00 IST):

1. `fetch_prices` — pulls all 10 coins in a single CoinGecko `/coins/markets`
   call, pushes rows via XCom
2. `load_to_snowflake` — creates the raw table if missing, inserts fetched
   rows (append-only, no dedup at this layer)
3. `dbt deps && dbt run && dbt test` — installs dbt packages, builds all
   models, runs all tests

Retries: 3, with exponential backoff.

## Tech stack

| Layer | Choice |
|---|---|
| Source data | Crypto prices via CoinGecko free API (no key required) |
| Orchestration | Apache Airflow 3.3.1, via Docker (docker-compose) |
| Warehouse | Snowflake — dedicated `CRYPTO_ANALYTICS_DB`, dedicated `CRYPTO_ANALYTICS_ROLE`, shared `SEC_PIPELINE_WH` compute |
| Transformation | dbt-core + dbt-snowflake — staging → intermediate → marts |
| Testing | Native dbt tests + `dbt_utils` |
| Coins | BTC, ETH, XRP, BNB, SOL, ADA, DOGE, TRX, AVAX, LINK (10 fixed large-caps, stablecoins excluded) |

## Star schema

- `fct_crypto_price` — grain: one row per coin per day
- `dim_coin`
- `dim_date`

## Getting started

```bash
cp .env.example .env        # fill in Snowflake credentials
docker compose up --build   # first run also creates the airflow admin user
```

Airflow UI: http://localhost:8080 (user/pass: `airflow` / `airflow`, from
`airflow-init` — change this before anything but local dev).

The `crypto_pipeline` DAG runs `fetch_prices` → `load_to_snowflake` → `dbt_run`
(which also runs `dbt test`) on a daily schedule.

## dbt project

Lives in `dbt_crypto_analytics/`. To run locally outside Docker, copy
`profiles.yml.example` to `~/.dbt/profiles.yml` and export the Snowflake env
vars referenced in it.

## Status

See `project3-status.md` (tracked in the companion Claude Project, not this
repo) for current build status and open decisions.

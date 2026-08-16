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

| Model | Type | Source | Grain / notes |
|---|---|---|---|
| `dim_coin` | Dimension | Static seed (`seeds/dim_coin_seed.csv`) | Fixed 10-coin list, surrogate `coin_key` |
| `dim_date` | Dimension | Generated (`dbt_utils.date_spine`) | Full date spine, 2020-01-01 → 2030-12-31 |
| `fct_crypto_price` | Fact | Inner-joins `int_crypto_daily_change` against both dims | One row per coin per day; rows failing to match either dim are dropped, not passed through with a null key |

## Data model layers

| Layer | Model | What it does |
|---|---|---|
| Staging | `stg_crypto_prices` | Incremental model, deduped on `coin_id + price_date` via surrogate `price_id`; merge strategy turns same-day re-triggers into upserts instead of duplicate rows |
| Intermediate | `int_crypto_daily_change` | Adds a self-computed day-over-day % price change via `LAG()`, alongside CoinGecko's own trailing-24h % change for reference (related but not the same calculation — see model docs) |
| Marts | `dim_coin`, `dim_date`, `fct_crypto_price` | Final star schema, ready for querying |

## Project structure

```
.
├── dags/
│   ├── crypto_pipeline_dag.py
│   └── scripts/
│       ├── fetch_prices.py
│       └── load_to_snowflake.py
├── dbt_crypto_analytics/
│   ├── seeds/
│   │   └── dim_coin_seed.csv
│   └── models/
│       ├── staging/
│       │   ├── sources.yml
│       │   ├── stg_crypto_prices.sql
│       │   └── stg_crypto_prices.yml
│       ├── intermediate/
│       │   ├── int_crypto_daily_change.sql
│       │   └── int_crypto_daily_change.yml
│       └── marts/
│           ├── dim_coin.sql
│           ├── dim_date.sql
│           ├── fct_crypto_price.sql
│           └── marts.yml
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Running locally

1. Copy `.env.example` to `.env` and fill in Snowflake credentials
   (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`,
   `SNOWFLAKE_ROLE`, `SNOWFLAKE_WAREHOUSE`)
2. `docker compose up -d` — brings up Postgres, Airflow api-server,
   scheduler, dag-processor, and triggerer (6 containers total)
3. Open the Airflow UI at `http://localhost:8080`
4. Unpause `crypto_pipeline_dag` and trigger a manual run to validate,
   or let it run on its `30 0 * * *` UTC schedule

**Note:** the DAG only runs while the containers are up — there's no
catch-up for runs missed while Docker is down (`catchup=False`).

## Known limitations / open items

- No backfill strategy — `dim_date` covers a wide static range, but historic
  price data isn't backfilled; the fact table only fills in from whenever
  the DAG started running
- Single daily snapshot per coin — not a true intraday time series
- `day_over_day_pct_change` will be `null` for a coin's first day of data
  (no prior snapshot to compare against)
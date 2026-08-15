# crypto-airflow-dbt-pipeline

A scheduled, retry-aware ELT pipeline for crypto market data: CoinGecko →
Snowflake → dbt, orchestrated end-to-end by Airflow running in Docker.

Companion project to [`stock-market-dbt-pipeline`](#) (P2), which proved the
dbt data-modeling pattern with manual runs. This project proves the pipeline
can be operationalized — scheduled, retried, monitored.

## Stack

- **Source**: CoinGecko free API (10 fixed coins — see `dags/scripts/coins.py`)
- **Orchestration**: Apache Airflow via `docker-compose`
- **Warehouse**: Snowflake (`CRYPTO_ANALYTICS_DB`, account `DJPBQEV-CK77560`)
- **Transformation**: dbt-core + dbt-snowflake (staging → intermediate → marts)
- **Testing**: native dbt tests, `dbt_utils`, `dbt_expectations`

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

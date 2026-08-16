"""
crypto_pipeline_dag.py

Daily pipeline: fetch coin prices from CoinGecko -> load raw rows into
Snowflake -> trigger dbt run (staging -> intermediate -> marts).

Grain: one row per coin per day (see project3-status.md).
Coins: BTC, ETH, XRP, BNB, SOL, ADA, DOGE, TRX, AVAX, LINK (fixed set, see
dags/scripts/coins.py).
"""
from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator

from scripts.fetch_prices import fetch_daily_prices
from scripts.load_to_snowflake import load_raw_prices

default_args = {
    "owner": "rishi",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "email_on_failure": False,  # flip on + add `email` key once alerting is wired up
}

with DAG(
    dag_id="crypto_pipeline",
    description="CoinGecko -> Snowflake -> dbt, daily",
    default_args=default_args,
    schedule="30 0 * * *", 
    start_date=datetime(2026, 8, 14),
    catchup=False,
    max_active_runs=1,
    tags=["crypto", "p3"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_prices",
        python_callable=fetch_daily_prices,
    )

    load_task = PythonOperator(
        task_id="load_to_snowflake",
        python_callable=load_raw_prices,
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run",
        cwd="/opt/airflow/dbt_crypto_analytics",
        bash_command=(
            "dbt deps --profiles-dir /opt/airflow/dbt_crypto_analytics && "
            "dbt run --profiles-dir /opt/airflow/dbt_crypto_analytics && "
            "dbt test --profiles-dir /opt/airflow/dbt_crypto_analytics"
        ),
    )

    fetch_task >> load_task >> dbt_run_task
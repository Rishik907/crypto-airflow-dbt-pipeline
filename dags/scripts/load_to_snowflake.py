"""
Load task: takes the rows fetched by fetch_prices and writes them into
CRYPTO_ANALYTICS_DB.RAW.CRYPTO_PRICES_RAW.

Table is created on first run if it doesn't exist. Same account as P2
(DJPBQEV-CK77560), new database.
"""
import os

import snowflake.connector

RAW_TABLE = "CRYPTO_ANALYTICS_DB.RAW.CRYPTO_PRICES_RAW"

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
    coin_id VARCHAR,
    symbol VARCHAR,
    price_usd FLOAT,
    market_cap_usd FLOAT,
    price_change_pct_24h FLOAT,
    fetched_at TIMESTAMP_NTZ
)
"""

INSERT_SQL = f"""
INSERT INTO {RAW_TABLE}
    (coin_id, symbol, price_usd, market_cap_usd, price_change_pct_24h, fetched_at)
VALUES (%(coin_id)s, %(symbol)s, %(price_usd)s, %(market_cap_usd)s,
        %(price_change_pct_24h)s, %(fetched_at)s)
"""


def _get_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database="CRYPTO_ANALYTICS_DB",
        schema="RAW",
    )


def load_raw_prices(**context):
    rows = context["ti"].xcom_pull(task_ids="fetch_prices", key="price_rows")
    if not rows:
        raise ValueError("No rows received from fetch_prices task")

    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        cur.executemany(INSERT_SQL, rows)
        conn.commit()
    finally:
        conn.close()

    return len(rows)

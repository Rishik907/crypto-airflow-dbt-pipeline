{{ config(
    materialized='incremental',
    unique_key='price_id',
    on_schema_change='sync_all_columns'
) }}

with source as (
    select *
    from {{ source('raw', 'crypto_prices_raw') }}

    {% if is_incremental() %}
    where fetched_at > (select coalesce(max(fetched_at), '1900-01-01') from {{ this }})
    {% endif %}
),
renamed as (
    select
        coin_id,
        symbol,
        price_usd,
        market_cap_usd,
        price_change_pct_24h,
        fetched_at,
        date(fetched_at) as price_date,
        {{ dbt_utils.generate_surrogate_key(['coin_id', 'date(fetched_at)']) }} as price_id
    from source
),
deduped as (
    select *
    from renamed
    qualify row_number() over (
        partition by coin_id, price_date
        order by fetched_at desc
    ) = 1
)
select * from deduped
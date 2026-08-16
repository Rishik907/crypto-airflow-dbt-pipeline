{{ config(materialized='view') }}
with staged as (
    select *
    from {{ ref('stg_crypto_prices') }}
),
with_previous as (
    select
        *,
        lag(price_usd) over (
            partition by coin_id
            order by price_date
        ) as prev_price_usd
    from staged
),
final as (
    select
        price_id,
        coin_id,
        symbol,
        price_date,
        price_usd,
        market_cap_usd,
        price_change_pct_24h as coingecko_pct_change_24h,
        prev_price_usd,
        case
            when prev_price_usd is null then null
            when prev_price_usd = 0 then null
            else round((price_usd - prev_price_usd) / prev_price_usd * 100, 4)
        end as day_over_day_pct_change
    from with_previous

)

select * from final
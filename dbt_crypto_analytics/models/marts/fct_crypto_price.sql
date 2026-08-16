{{ config(materialized='table') }}

with daily_change as (

    select *
    from {{ ref('int_crypto_daily_change') }}

),

coin as (

    select coin_id, coin_key
    from {{ ref('dim_coin') }}

),

date_dim as (

    select price_date, date_key
    from {{ ref('dim_date') }}

),

final as (

    select
        daily_change.price_id,
        coin.coin_key,
        date_dim.date_key,
        daily_change.price_usd,
        daily_change.market_cap_usd,
        daily_change.coingecko_pct_change_24h,
        daily_change.prev_price_usd,
        daily_change.day_over_day_pct_change

    from daily_change
    inner join coin
        on daily_change.coin_id = coin.coin_id
    inner join date_dim
        on daily_change.price_date = date_dim.price_date

)

select * from final
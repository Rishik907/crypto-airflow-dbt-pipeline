{{ config(materialized='table') }}

select
    coin_id,
    symbol,
    coin_name,
    {{ dbt_utils.generate_surrogate_key(['coin_id']) }} as coin_key
from {{ ref('dim_coin_seed') }}
{{ config(materialized='table') }}

with spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2020-01-01' as date)",
        end_date="cast('2031-01-01' as date)"
    ) }}

),

final as (

    select
        date_day as price_date,
        {{ dbt_utils.generate_surrogate_key(['date_day']) }} as date_key,
        year(date_day) as year,
        month(date_day) as month,
        day(date_day) as day,
        dayofweek(date_day) as day_of_week,
        dayname(date_day) as day_name,
        monthname(date_day) as month_name,
        quarter(date_day) as quarter,
        case when dayofweek(date_day) in (0, 6) then true else false end as is_weekend

    from spine

)

select * from final
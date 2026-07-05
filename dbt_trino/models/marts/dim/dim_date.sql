{{ config(
    materialized='table',
    format='PARQUET',
    alias='dim_date'
) }}

with date_range as (
    select date_day
    from unnest(sequence(date '2020-01-01', date '2030-12-31', interval '1' day)) as t(date_day)
)

select
    date_day as date_key,
    extract(year from date_day) as year,
    extract(quarter from date_day) as quarter,
    extract(month from date_day) as month,
    extract(day from date_day) as day_of_month,
    extract(dow from date_day) as day_of_week,
    extract(doy from date_day) as day_of_year,
    date_format(date_day, '%Y-%m') as year_month,
    date_format(date_day, '%Y-Q%v') as year_quarter,
    date_format(date_day, '%W') as day_name,
    date_format(date_day, '%M') as month_name,
    case when extract(dow from date_day) in (6, 7) then 1 else 0 end as is_weekend_flag
from date_range

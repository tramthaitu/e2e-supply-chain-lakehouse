{{ config(
    materialized='table',
    format='PARQUET',
    alias='dim_promotions'
) }}

with promos as (
    select * from {{ ref('stg_promotions') }}
)

select
    promo_id,
    promo_name,
    promo_type,
    discount_value,
    start_date,
    end_date,
    applicable_category,
    promo_channel,
    stackable_flag,
    min_order_value,
    date_diff('day', start_date, end_date) as promo_duration_days
from promos

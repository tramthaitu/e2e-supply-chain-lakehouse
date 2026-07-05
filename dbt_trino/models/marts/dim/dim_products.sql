{{ config(
    materialized='table',
    format='PARQUET',
    alias='dim_products'
) }}

with products as (
    select * from {{ ref('stg_products') }}
)

select
    product_id,
    product_name,
    category,
    segment,
    size,
    color,
    price,
    cogs,
    (price - cogs) as gross_margin,
    round((price - cogs) / nullif(price, 0) * 100, 2) as gross_margin_pct
from products

{{ config(
    materialized='table',
    format='PARQUET',
    alias='fct_return_items'
) }}

with returns as (
    select * from {{ ref('stg_returns') }}
),

orders as (
    select order_id, order_date, customer_id, zip from {{ ref('stg_orders') }}
),

products as (
    select product_id, price, cogs from {{ ref('dim_products') }}
)

select
    r.return_id,
    r.order_id,
    o.order_date,
    r.return_date,
    r.product_id,
    o.customer_id,
    o.zip,
    r.return_reason,
    r.return_quantity,
    r.refund_amount,
    (r.return_quantity * p.cogs) as returned_inventory_cogs,
    (r.refund_amount - (r.return_quantity * p.cogs)) as net_reverse_logistics_loss,
    date_diff('day', o.order_date, r.return_date) as days_from_order_to_return
from returns r
left join orders o on r.order_id = o.order_id
left join products p on r.product_id = p.product_id

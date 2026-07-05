{{ config(
    materialized='table',
    format='PARQUET',
    alias='fct_logistics_delivery_performance'
) }}

with fulfillment as (
    select * from {{ ref('fct_order_fulfillment') }}
    where order_status in ('shipped', 'delivered', 'returned')
),

customers as (
    select * from {{ ref('dim_customers') }}
)

select
    date_trunc('month', f.order_date) as performance_month,
    c.region,
    c.district,
    c.city,
    count(f.order_id) as total_shipments,
    round(avg(f.processing_days), 2) as avg_warehouse_processing_days,
    round(avg(f.shipping_transit_days), 2) as avg_carrier_transit_days,
    round(avg(f.total_fulfillment_days), 2) as avg_total_fulfillment_days,
    sum(f.shipping_fee) as total_logistics_revenue,
    sum(f.returned_qty) as total_returned_items,
    sum(f.refund_amount) as total_reverse_logistics_refunds,
    round(cast(sum(f.is_returned_flag) as double) / nullif(count(f.order_id), 0) * 100, 2) as return_rate_pct,
    round(avg(f.customer_rating), 2) as regional_csat_rating
from fulfillment f
left join customers c on f.customer_id = c.customer_id
group by 1, 2, 3, 4

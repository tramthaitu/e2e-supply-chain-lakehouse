{{ config(
    materialized='incremental',
    format='PARQUET',
    incremental_strategy='merge',
    unique_key='order_id',
    alias='fct_order_fulfillment'
) }}

with orders as (
    select * from {{ ref('stg_orders') }}
    {% if is_incremental() %}
    where order_date >= (select coalesce(max(order_date), cast('1900-01-01' as date)) from {{ this }})
    {% endif %}
),

shipments as (
    select * from {{ ref('stg_shipments') }}
),

payments as (
    select * from {{ ref('stg_payments') }}
),

returns as (
    select
        order_id,
        sum(return_quantity) as total_returned_qty,
        sum(refund_amount) as total_refund_amount
    from {{ ref('stg_returns') }}
    group by order_id
),

reviews as (
    select
        order_id,
        avg(rating) as avg_rating
    from {{ ref('stg_reviews') }}
    group by order_id
)

select
    o.order_id,
    o.order_date,
    o.customer_id,
    o.order_status,
    p.payment_method,
    coalesce(p.payment_value, 0.0) as payment_value,
    coalesce(p.installments, 1) as installments,
    s.ship_date,
    s.delivery_date,
    coalesce(s.shipping_fee, 0.0) as shipping_fee,
    date_diff('day', o.order_date, s.ship_date) as processing_days,
    date_diff('day', s.ship_date, s.delivery_date) as shipping_transit_days,
    date_diff('day', o.order_date, s.delivery_date) as total_fulfillment_days,
    coalesce(r.total_returned_qty, 0) as returned_qty,
    coalesce(r.total_refund_amount, 0.0) as refund_amount,
    case when r.total_returned_qty > 0 then 1 else 0 end as is_returned_flag,
    rev.avg_rating as customer_rating
from orders o
left join payments p on o.order_id = p.order_id
left join shipments s on o.order_id = s.order_id
left join returns r on o.order_id = r.order_id
left join reviews rev on o.order_id = rev.order_id

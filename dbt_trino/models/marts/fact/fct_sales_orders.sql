{{ config(
    materialized='incremental',
    format='PARQUET',
    incremental_strategy='merge',
    unique_key='order_id',
    alias='fct_sales_orders'
) }}

with orders as (
    select * from {{ ref('stg_orders') }}
    {% if is_incremental() %}
    where order_date >= (select coalesce(max(order_date), cast('1900-01-01' as date)) from {{ this }})
    {% endif %}
),

order_items_summary as (
    select
        order_id,
        sum(quantity) as total_items,
        sum(quantity * original_unit_price) as gross_order_value,
        sum(calculated_discount_amount) as total_discount,
        sum(net_line_total) as net_order_value
    from {{ ref('int_order_items_discounted') }}
    group by order_id
)

select
    o.order_id,
    o.order_date,
    o.customer_id,
    o.zip,
    o.order_status,
    o.payment_method,
    o.device_type,
    o.order_source,
    coalesce(s.total_items, 0) as total_items,
    coalesce(s.gross_order_value, 0.0) as gross_order_value,
    coalesce(s.total_discount, 0.0) as total_discount,
    coalesce(s.net_order_value, 0.0) as net_order_value
from orders o
left join order_items_summary s on o.order_id = s.order_id

{{ config(
    materialized='table',
    format='PARQUET',
    alias='rpt_daily_category_sales_performance'
) }}

with order_items as (
    select * from {{ ref('int_order_items_discounted') }}
),

orders as (
    select order_id, order_date from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('dim_products') }}
)

select
    o.order_date as report_date,
    p.category,
    p.segment,
    count(distinct i.order_id) as orders_containing_category,
    sum(i.quantity) as total_units_sold,
    sum(i.quantity * i.original_unit_price) as category_gross_revenue,
    sum(i.calculated_discount_amount) as category_total_discount,
    sum(i.net_line_total) as category_net_revenue,
    sum(i.net_line_total - (i.quantity * p.cogs)) as category_gross_profit,
    round(sum(i.net_line_total - (i.quantity * p.cogs)) / nullif(sum(i.net_line_total), 0) * 100, 2) as category_profit_margin_pct
from order_items i
join orders o on i.order_id = o.order_id
join products p on i.product_id = p.product_id
group by 1, 2, 3

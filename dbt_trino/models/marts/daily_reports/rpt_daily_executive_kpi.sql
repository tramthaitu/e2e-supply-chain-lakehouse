{{ config(
    materialized='table',
    format='PARQUET',
    alias='rpt_daily_executive_kpi'
) }}

with daily_sales as (
    select
        order_date as report_date,
        count(distinct order_id) as total_orders_placed,
        count(distinct customer_id) as buying_customers,
        sum(gross_order_value) as gross_revenue,
        sum(total_discount) as total_discount_given,
        sum(net_order_value) as net_revenue,
        round(sum(net_order_value) / nullif(count(distinct order_id), 0), 2) as average_order_value
    from {{ ref('fct_sales_orders') }}
    group by order_date
),

daily_shipments as (
    select
        ship_date as report_date,
        count(distinct order_id) as orders_shipped_today,
        sum(shipping_fee) as shipping_revenue_today
    from {{ ref('stg_shipments') }}
    where ship_date is not null
    group by ship_date
),

daily_deliveries as (
    select
        delivery_date as report_date,
        count(distinct order_id) as orders_delivered_today
    from {{ ref('stg_shipments') }}
    where delivery_date is not null
    group by delivery_date
),

daily_returns as (
    select
        return_date as report_date,
        count(distinct return_id) as returns_requested_today,
        sum(return_quantity) as return_items_today,
        sum(refund_amount) as total_refunds_today
    from {{ ref('stg_returns') }}
    where return_date is not null
    group by return_date
)

select
    coalesce(s.report_date, sh.report_date, d.report_date, r.report_date) as report_date,
    coalesce(s.total_orders_placed, 0) as total_orders_placed,
    coalesce(s.buying_customers, 0) as buying_customers,
    coalesce(s.gross_revenue, 0.0) as gross_revenue,
    coalesce(s.total_discount_given, 0.0) as total_discount_given,
    coalesce(s.net_revenue, 0.0) as net_revenue,
    coalesce(s.average_order_value, 0.0) as average_order_value,
    coalesce(sh.orders_shipped_today, 0) as orders_shipped_today,
    coalesce(sh.shipping_revenue_today, 0.0) as shipping_revenue_today,
    coalesce(d.orders_delivered_today, 0) as orders_delivered_today,
    coalesce(r.returns_requested_today, 0) as returns_requested_today,
    coalesce(r.return_items_today, 0) as return_items_today,
    coalesce(r.total_refunds_today, 0.0) as total_refunds_today,
    coalesce(s.net_revenue, 0.0) - coalesce(r.total_refunds_today, 0.0) as daily_realized_cashflow
from daily_sales s
full outer join daily_shipments sh on s.report_date = sh.report_date
full outer join daily_deliveries d on coalesce(s.report_date, sh.report_date) = d.report_date
full outer join daily_returns r on coalesce(s.report_date, sh.report_date, d.report_date) = r.report_date

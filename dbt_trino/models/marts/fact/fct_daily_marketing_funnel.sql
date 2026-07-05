{{ config(
    materialized='table',
    format='PARQUET',
    alias='fct_daily_marketing_funnel'
) }}

with traffic as (
    select * from {{ ref('stg_web_traffic') }}
),

daily_orders as (
    select
        order_date,
        count(distinct order_id) as total_orders,
        count(distinct customer_id) as buying_customers
    from {{ ref('stg_orders') }}
    group by order_date
),

daily_sales as (
    select
        order_date,
        sum(net_order_value) as daily_net_revenue
    from {{ ref('fct_sales_orders') }}
    group by order_date
)

select
    t.traffic_date,
    t.traffic_source,
    t.sessions,
    t.unique_visitors,
    t.page_views,
    t.bounce_rate,
    t.avg_session_duration_sec,
    coalesce(o.total_orders, 0) as total_orders,
    coalesce(o.buying_customers, 0) as buying_customers,
    coalesce(s.daily_net_revenue, 0.0) as daily_net_revenue,
    round(coalesce(o.total_orders, 0) / nullif(cast(t.sessions as double), 0) * 100, 2) as session_conversion_rate_pct,
    round(coalesce(s.daily_net_revenue, 0.0) / nullif(cast(t.unique_visitors as double), 0), 2) as revenue_per_visitor
from traffic t
left join daily_orders o on t.traffic_date = o.order_date
left join daily_sales s on t.traffic_date = s.order_date

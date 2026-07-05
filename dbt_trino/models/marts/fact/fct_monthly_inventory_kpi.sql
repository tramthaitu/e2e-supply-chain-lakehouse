{{ config(
    materialized='table',
    format='PARQUET',
    alias='fct_monthly_inventory_kpi'
) }}

with inv as (
    select * from {{ ref('stg_inventory') }}
),

prod as (
    select * from {{ ref('dim_products') }}
)

select
    i.snapshot_date,
    i.year,
    i.month,
    i.product_id,
    coalesce(i.product_name, p.product_name) as product_name,
    coalesce(i.category, p.category) as category,
    coalesce(i.segment, p.segment) as segment,
    p.price,
    p.cogs,
    i.stock_on_hand,
    i.units_received,
    i.units_sold,
    (i.stock_on_hand * p.cogs) as inventory_holding_value,
    (i.units_sold * (p.price - p.cogs)) as monthly_realized_profit,
    i.stockout_days,
    i.days_of_supply,
    i.fill_rate,
    i.sell_through_rate,
    i.stockout_flag,
    i.overstock_flag,
    i.reorder_flag,
    case
        when i.stockout_days > 0 then round((i.units_sold / nullif(30.0 - i.stockout_days, 0)) * i.stockout_days * p.price, 2)
        else 0.0
    end as estimated_lost_revenue_due_to_stockout
from inv i
left join prod p on i.product_id = p.product_id

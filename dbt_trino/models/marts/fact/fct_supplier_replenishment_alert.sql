{{ config(
    materialized='table',
    format='PARQUET',
    alias='fct_supplier_replenishment_alert'
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
    p.product_name,
    p.category,
    p.segment,
    i.stock_on_hand,
    i.units_sold,
    i.units_received,
    i.days_of_supply,
    i.fill_rate,
    i.stockout_days,
    i.stockout_flag,
    i.overstock_flag,
    i.reorder_flag,
    round(i.units_sold / 30.0, 2) as daily_burn_rate,
    case
        when i.stockout_flag = 1 or i.days_of_supply < 10 then 'CRITICAL_STOCKOUT_RISK'
        when i.reorder_flag = 1 or i.days_of_supply between 10 and 20 then 'REORDER_IMMEDIATELY'
        when i.overstock_flag = 1 then 'EXCESS_OVERSTOCK'
        else 'HEALTHY_BUFFER'
    end as supply_chain_action_status,
    case
        when i.reorder_flag = 1 or i.stockout_flag = 1 then greatest(cast((i.units_sold * 1.5) - i.stock_on_hand as integer), 0)
        else 0
    end as recommended_reorder_qty
from inv i
left join prod p on i.product_id = p.product_id

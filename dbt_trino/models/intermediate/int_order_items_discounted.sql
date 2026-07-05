{{ config(
    materialized='table',
    alias='int_order_items_discounted'
) }}

with items as (
    select * from {{ ref('stg_order_items') }}
),

promos as (
    select * from {{ ref('stg_promotions') }}
),

joined as (
    select
        i.order_id,
        i.product_id,
        i.quantity,
        i.unit_price as original_unit_price,
        i.promo_id,
        i.promo_id_2,
        p.promo_type,
        p.discount_value,
        case
            when p.promo_type = 'percentage' then i.quantity * i.unit_price * (p.discount_value / 100.0)
            when p.promo_type = 'fixed' then i.quantity * p.discount_value
            else coalesce(i.discount_amount, 0.0)
        end as calculated_discount_amount
    from items i
    left join promos p on i.promo_id = p.promo_id
)

select
    order_id,
    product_id,
    quantity,
    original_unit_price,
    promo_id,
    promo_id_2,
    calculated_discount_amount,
    (quantity * original_unit_price) - calculated_discount_amount as net_line_total
from joined

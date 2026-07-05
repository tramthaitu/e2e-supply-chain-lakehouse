{{ config(
    materialized='table',
    alias='stg_order_items'
) }}

with source as (
    select * from {{ source('landing', 'sales_order_items') }}
),

renamed as (
    select
        cast(order_id as integer) as order_id,
        cast(product_id as integer) as product_id,
        cast(quantity as integer) as quantity,
        cast(unit_price as double) as unit_price,
        cast(discount_amount as double) as discount_amount,
        nullif(trim(promo_id), '') as promo_id,
        nullif(trim(promo_id_2), '') as promo_id_2
    from source
    where order_id is not null and product_id is not null
)

select * from renamed

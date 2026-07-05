{{ config(
    materialized='table',
    alias='stg_shipments'
) }}

with source as (
    select * from {{ source('landing', 'supply_chain_shipments') }}
),

renamed as (
    select
        cast(order_id as integer) as order_id,
        cast(ship_date as date) as ship_date,
        cast(delivery_date as date) as delivery_date,
        cast(shipping_fee as double) as shipping_fee
    from source
    where order_id is not null
)

select * from renamed

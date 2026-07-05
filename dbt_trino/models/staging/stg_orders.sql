{{ config(
    materialized='table',
    alias='stg_orders'
) }}

with source as (
    select * from {{ source('landing', 'sales_orders') }}
),

renamed as (
    select
        cast(order_id as integer) as order_id,
        cast(order_date as date) as order_date,
        cast(customer_id as integer) as customer_id,
        cast(zip as integer) as zip,
        lower(trim(order_status)) as order_status,
        trim(payment_method) as payment_method,
        trim(device_type) as device_type,
        trim(order_source) as order_source
    from source
    where order_id is not null
)

select * from renamed

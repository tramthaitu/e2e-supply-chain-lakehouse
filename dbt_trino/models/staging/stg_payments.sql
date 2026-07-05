{{ config(
    materialized='table',
    alias='stg_payments'
) }}

with source as (
    select * from {{ source('landing', 'sales_payments') }}
),

renamed as (
    select
        cast(order_id as integer) as order_id,
        trim(payment_method) as payment_method,
        cast(payment_value as double) as payment_value,
        cast(installments as integer) as installments
    from source
    where order_id is not null
)

select * from renamed

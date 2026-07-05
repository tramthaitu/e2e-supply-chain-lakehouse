{{ config(
    materialized='table',
    alias='stg_returns'
) }}

with source as (
    select * from {{ source('landing', 'sales_returns') }}
),

renamed as (
    select
        trim(return_id) as return_id,
        cast(order_id as integer) as order_id,
        cast(product_id as integer) as product_id,
        cast(return_date as date) as return_date,
        trim(return_reason) as return_reason,
        cast(return_quantity as integer) as return_quantity,
        cast(refund_amount as double) as refund_amount
    from source
    where return_id is not null
)

select * from renamed

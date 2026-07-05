{{ config(
    materialized='table',
    alias='stg_products'
) }}

with source as (
    select * from {{ source('landing', 'master_data_products') }}
),

renamed as (
    select
        cast(product_id as integer) as product_id,
        trim(product_name) as product_name,
        trim(category) as category,
        trim(segment) as segment,
        trim(size) as size,
        trim(color) as color,
        cast(price as double) as price,
        cast(cogs as double) as cogs
    from source
    where product_id is not null
)

select * from renamed

{{ config(
    materialized='table',
    alias='stg_promotions'
) }}

with source as (
    select * from {{ source('landing', 'master_data_promotions') }}
),

renamed as (
    select
        trim(promo_id) as promo_id,
        trim(promo_name) as promo_name,
        lower(trim(promo_type)) as promo_type,
        cast(discount_value as double) as discount_value,
        cast(start_date as date) as start_date,
        cast(end_date as date) as end_date,
        trim(applicable_category) as applicable_category,
        trim(promo_channel) as promo_channel,
        cast(stackable_flag as integer) as stackable_flag,
        cast(min_order_value as double) as min_order_value
    from source
    where promo_id is not null
)

select * from renamed

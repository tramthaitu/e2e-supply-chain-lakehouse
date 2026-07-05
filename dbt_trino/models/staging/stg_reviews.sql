{{ config(
    materialized='table',
    alias='stg_reviews'
) }}

with source as (
    select * from {{ source('landing', 'marketing_reviews') }}
),

renamed as (
    select
        trim(review_id) as review_id,
        cast(order_id as integer) as order_id,
        cast(product_id as integer) as product_id,
        cast(customer_id as integer) as customer_id,
        cast(review_date as date) as review_date,
        cast(rating as integer) as rating,
        trim(review_title) as review_title
    from source
    where review_id is not null
)

select * from renamed

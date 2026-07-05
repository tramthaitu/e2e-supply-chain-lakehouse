{{ config(
    materialized='table',
    format='PARQUET',
    alias='fct_customer_reviews'
) }}

with reviews as (
    select * from {{ ref('stg_reviews') }}
),

orders as (
    select order_id, order_date, order_source from {{ ref('stg_orders') }}
)

select
    r.review_id,
    r.order_id,
    o.order_date,
    r.review_date,
    r.product_id,
    r.customer_id,
    r.rating,
    r.review_title,
    o.order_source,
    date_diff('day', o.order_date, r.review_date) as days_to_review,
    case
        when r.rating >= 4 then 'Positive'
        when r.rating = 3 then 'Neutral'
        else 'Negative_Detractor'
    end as csat_sentiment_category
from reviews r
left join orders o on r.order_id = o.order_id

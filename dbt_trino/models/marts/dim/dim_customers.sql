{{ config(
    materialized='table',
    format='PARQUET',
    alias='dim_customers'
) }}

with customers as (
    select * from {{ ref('stg_customers') }}
),

geo as (
    select * from {{ ref('stg_geography') }}
)

select
    c.customer_id,
    c.zip,
    coalesce(c.city, g.city) as city,
    g.region,
    g.district,
    c.signup_date,
    c.gender,
    c.age_group,
    c.acquisition_channel,
    date_diff('day', c.signup_date, current_date) as customer_tenure_days
from customers c
left join geo g on c.zip = g.zip

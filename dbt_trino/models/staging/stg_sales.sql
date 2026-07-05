{{ config(
    materialized='table',
    alias='stg_sales'
) }}

with source as (
    select * from {{ source('landing', 'sales_sales') }}
)

select
    cast(date as date) as sales_date,
    cast(revenue as double) as revenue,
    cast(cogs as double) as cogs
from source

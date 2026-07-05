{{ config(
    materialized='table',
    format='PARQUET',
    alias='dim_geography'
) }}

with geo as (
    select * from {{ ref('stg_geography') }}
)

select
    zip,
    city,
    district,
    region,
    concat(city, ' - ', district) as city_district_label
from geo

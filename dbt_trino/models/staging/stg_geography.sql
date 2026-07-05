{{ config(
    materialized='table',
    alias='stg_geography'
) }}

with source as (
    select * from {{ source('landing', 'master_data_geography') }}
),

renamed as (
    select
        cast(zip as integer) as zip,
        trim(city) as city,
        trim(region) as region,
        trim(district) as district
    from source
    where zip is not null
)

select * from renamed

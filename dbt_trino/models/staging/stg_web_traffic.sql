{{ config(
    materialized='table',
    alias='stg_web_traffic'
) }}

with source as (
    select * from {{ source('landing', 'marketing_web_traffic') }}
),

renamed as (
    select
        cast(date as date) as traffic_date,
        cast(sessions as integer) as sessions,
        cast(unique_visitors as integer) as unique_visitors,
        cast(page_views as integer) as page_views,
        cast(bounce_rate as double) as bounce_rate,
        cast(avg_session_duration_sec as double) as avg_session_duration_sec,
        trim(traffic_source) as traffic_source
    from source
    where date is not null
)

select * from renamed

{{ config(
    materialized='table',
    alias='stg_customers'
) }}

with source as (
    select * from {{ source('landing', 'master_data_customers') }}
),

renamed as (
    select
        cast(customer_id as integer) as customer_id,
        cast(zip as integer) as zip,
        trim(city) as city,
        cast(signup_date as date) as signup_date,
        trim(gender) as gender,
        trim(age_group) as age_group,
        trim(acquisition_channel) as acquisition_channel
    from source
    where customer_id is not null
)

select * from renamed

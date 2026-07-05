{% snapshot snp_customers %}

{{
    config(
        target_database='iceberg',
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols=['city', 'zip', 'age_group', 'acquisition_channel']
    )
}}

select * from {{ source('landing', 'master_data_customers') }}

{% endsnapshot %}

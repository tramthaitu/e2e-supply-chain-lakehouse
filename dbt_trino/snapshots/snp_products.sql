{% snapshot snp_products %}

{{
    config(
        target_database='iceberg',
        target_schema='snapshots',
        unique_key='product_id',
        strategy='check',
        check_cols=['product_name', 'category', 'segment', 'price', 'cogs']
    )
}}

select * from {{ source('landing', 'master_data_products') }}

{% endsnapshot %}

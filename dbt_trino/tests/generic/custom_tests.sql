{% test left_join_null_check(
    model,
    join_key,
    helper_table,
    helper_key=None,
    check_column=None,
    warn_threshold=0,
    filter=None,
    helper_filter=None
) %}

{% set helper_key = helper_key if helper_key is not none else join_key %}
{% set check_col_name = check_column if check_column is not none else helper_key %}

with main as (
    select {{ join_key }}
    from {{ model }}
    {% if filter is not none %}
    where {{ filter }}
    {% endif %}
),

helper as (
    select
        {{ helper_key }}
        {% if check_col_name != helper_key %}
        , {{ check_col_name }}
        {% endif %}
    from {{ helper_table }}
    {% if helper_filter is not none %}
    where {{ helper_filter }}
    {% endif %}
),

joined as (
    select
        m.{{ join_key }},
        h.{{ check_col_name }} as matched_value
    from main m
    left join helper h
        on m.{{ join_key }} = h.{{ helper_key }}
),

agg as (
    select count(*) as null_count
    from joined
    where matched_value is null
)

select null_count
from agg
where null_count > {{ warn_threshold }}

{% endtest %}



{% test monthly_order_code_quality_warn(
    model,
    date_field=None,
    order_code_field=None,
    issue_type='DUPLICATE',
    updated_at_field=None,
    lookback_months=3,
    lookback_days=None,
    is_date_field_string=False
) %}

{# ---- defensive: make sure lookback_months is an int ---- #}
{% set lookback_months = (lookback_months | int) %}

{# ---- DATE expr: cast -> string -> left 10 -> cast date ---- #}
{% set date_expr = "cast(substr(cast(" ~ date_field ~ " as varchar), 1, 10) as date)" %}

{# ---- cutoff month date adapted for Trino SQL ---- #}
{% set cutoff_month_date = "date_trunc('month', date_add('month', -" ~ lookback_months ~ ", current_date))" %}

{% if issue_type == 'MAX_UPDATE' %}

{# ---- For partitioned tables, filter directly on the partition column ---- #}
{% if lookback_days is not none %}
  {% set cutoff_date = "date_add('day', -" ~ (lookback_days | int) ~ ", current_date)" %}
{% else %}
  {% set cutoff_date = cutoff_month_date %}
{% endif %}

select
  max({{ date_expr }}) as max_date,
  'MAX_UPDATE_TOO_OLD' as issue_type,
  date_diff('day', max({{ date_expr }}), current_date) as days_since_last_update
from {{ model }}
where
  {% if is_date_field_string %}
  {{ date_expr }} >= {{ cutoff_month_date }}
  {% else %}
  {{ date_field }} >= {{ cutoff_month_date }}
  {% endif %}
having
  max({{ date_expr }}) < {{ cutoff_date }}

{% else %}

select
  date_trunc('month', {{ date_expr }}) as month,
  'DUPLICATE_ORDER_CODE' as issue_type,
  count({{ order_code_field }}) - count(distinct {{ order_code_field }}) as issue_count
from {{ model }}
where
  {% if is_date_field_string %}
  {{ date_expr }} >= {{ cutoff_month_date }}
  {% else %}
  {{ date_field }} >= {{ cutoff_month_date }}
  {% endif %}
group by 1, 2
having
  count({{ order_code_field }}) != count(distinct {{ order_code_field }})

{% endif %}

{% endtest %}

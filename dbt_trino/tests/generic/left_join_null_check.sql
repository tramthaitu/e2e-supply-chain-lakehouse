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

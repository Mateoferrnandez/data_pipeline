
{% macro discounted_amount(extended_price,discount_percentage, scale=2) %}
    ( {{ extended_price }} * {{ discount_percentage }} / 100)::decimal(16, {{ scale }})
{% endmacro %}
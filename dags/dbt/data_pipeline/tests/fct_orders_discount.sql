select *
from
    {{ ref('fct_orders') }}
where
    item_discounted_amount < 0

    
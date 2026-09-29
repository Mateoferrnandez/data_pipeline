select
    *
from 
    {{ ref('fct_orders') }}
where
    date(order_date) > current_date
    or date(order_date) < date('1992-01-01')


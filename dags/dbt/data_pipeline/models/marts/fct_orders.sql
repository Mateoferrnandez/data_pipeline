select
    orders.*,
    orders_items_summary.gross_item_sales_amount,
    orders_items_summary.item_discounted_amount
from
    {{ ref('stg_tpch_orders') }} as orders
join
    {{ ref('int_order_items_summary') }} as orders_items_summary
    on orders.order_key = orders_items_summary.order_key
order by order_date

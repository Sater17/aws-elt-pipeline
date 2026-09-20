SELECT *
FROM {{ ref('fact_orders') }}
WHERE order_amount < 0
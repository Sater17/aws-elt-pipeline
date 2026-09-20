SELECT
    order_id,
    customer_id,
    product_id,
    CAST(order_date AS DATE) AS order_date,
    quantity,
    unit_price,
    quantity * unit_price AS order_amount,
    status
FROM {{ source('raw', 'raw_orders') }}
SELECT
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    unit_price,
    order_amount,
    status AS order_status,
    CASE
        WHEN status = 'completed' THEN TRUE
        ELSE FALSE
    END AS is_completed
FROM {{ ref('stg_orders') }}
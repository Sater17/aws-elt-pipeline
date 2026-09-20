SELECT
    order_date,
    COUNT(*) AS order_count,
    SUM(order_amount) AS total_sales,
    SUM(
        CASE
            WHEN order_status = 'completed'
            THEN order_amount
            ELSE 0
        END
    ) AS completed_sales
FROM {{ ref('fact_orders') }}
GROUP BY order_date
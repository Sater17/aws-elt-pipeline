SELECT
    customer_id,
    customer_name,
    email,
    country,
    CAST(signup_date AS DATE) AS signup_date
FROM {{ source('raw', 'raw_customers') }}
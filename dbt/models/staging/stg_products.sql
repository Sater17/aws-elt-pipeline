SELECT
    product_id,
    product_name,
    category,
    unit_price
FROM {{ source('raw', 'raw_products') }}
from dagster import asset

from ingestion.s3_to_postgres import load_csv


@asset
def raw_orders():
    load_csv(
        "data/sample/orders_2026-09-17.csv",
        "raw_orders",
    )


@asset
def raw_customers():
    load_csv(
        "data/sample/customers.csv",
        "raw_customers",
    )


@asset
def raw_products():
    load_csv(
        "data/sample/products.csv",
        "raw_products",
    )
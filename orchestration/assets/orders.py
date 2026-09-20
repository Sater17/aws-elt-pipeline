from dagster import asset, Config

from ingestion.s3_to_postgres import load_orders


class OrdersConfig(Config):
    file_path: str


@asset
def raw_orders(config: OrdersConfig):
    load_orders(config.file_path)
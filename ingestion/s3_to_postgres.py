import os
from pathlib import Path
import boto3
import pandas as pd
from sqlalchemy import create_engine, text
import tempfile
from pathlib import Path


POSTGRES_USER = os.getenv("POSTGRES_USER", "elt_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "elt_password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")
POSTGRES_DB = os.getenv("POSTGRES_DB", "elt_db")

s3_client = boto3.client("s3")

def download_s3_file(bucket_name, object_key, local_path):
    print(
        f"Downloading s3://{bucket_name}/{object_key}"
    )

    s3_client.download_file(
        bucket_name,
        object_key,
        str(local_path),
    )

    print(
        f"Downloaded to {local_path}"
    )


def get_postgres_engine():
    connection_url = (
        f"postgresql+psycopg2://"
        f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    return create_engine(connection_url)


def is_file_already_processed(
    engine,
    bucket_name,
    object_key,
    etag,
):
    query = text("""
        SELECT 1
        FROM ingestion_log
        WHERE bucket_name = :bucket_name
          AND object_key = :object_key
          AND etag = :etag
          AND status = 'SUCCESS'
        LIMIT 1
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {
                "bucket_name": bucket_name,
                "object_key": object_key,
                "etag": etag,
            },
        )

        return result.fetchone() is not None


def log_ingestion(
    engine,
    file_name,
    file_path,
    file_size,
    row_count,
    status,
    error_message=None,
    bucket_name=None,
    object_key=None,
    etag=None,
):
    query = text("""
        INSERT INTO ingestion_log (
            file_name,
            file_path,
            file_size,
            row_count,
            status,
            error_message,
            bucket_name,
            object_key,
            etag
        )
        VALUES (
            :file_name,
            :file_path,
            :file_size,
            :row_count,
            :status,
            :error_message,
            :bucket_name,
            :object_key,
            :etag
        )
    """)

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "file_name": file_name,
                "file_path": str(file_path),
                "file_size": file_size,
                "row_count": row_count,
                "status": status,
                "error_message": error_message,
                "bucket_name": bucket_name,
                "object_key": object_key,
                "etag": etag,
            },
        )


def load_csv(
    file_path,
    table_name,
    bucket_name=None,
    object_key=None,
    etag=None,
):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    file_name = file_path.name
    file_size = file_path.stat().st_size

    engine = get_postgres_engine()

    if is_file_already_processed(
        engine,
        bucket_name,
        object_key,
        etag,
    ):
        print(
            f"File already processed: "
            f"s3://{bucket_name}/{object_key}"
        )
        print("Skipping ingestion.")
        return

    try:
        df = pd.read_csv(file_path)

        print(
            f"Read {len(df)} rows from {file_path}"
        )

        df.to_sql(
            name=table_name,
            con=engine,
            schema="public",
            if_exists="append",
            index=False,
        )

        log_ingestion(
            engine=engine,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            row_count=len(df),
            status="SUCCESS",
            bucket_name=bucket_name,
            object_key=object_key,
            etag=etag,
        )

        print(
            f"Loaded {len(df)} rows "
            f"into public.{table_name}"
        )

        print("Ingestion status: SUCCESS")

    except Exception as e:
        log_ingestion(
            engine=engine,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            row_count=0,
            status="FAILED",
            error_message=str(e),
            bucket_name=bucket_name,
            object_key=object_key,
            etag=etag,
        )

        print(f"Ingestion failed: {e}")
        raise

def load_s3_csv(
    bucket_name,
    object_key,
    etag,
    table_name,
):
    engine = get_postgres_engine()

    # Check idempotency BEFORE downloading
    if is_file_already_processed(
        engine,
        bucket_name,
        object_key,
        etag,
    ):
        print(
            f"File already processed: "
            f"s3://{bucket_name}/{object_key}"
        )
        print("Skipping ingestion.")
        return

    file_name = Path(object_key).name

    with tempfile.TemporaryDirectory() as temp_dir:
        local_path = Path(temp_dir) / file_name

        try:
            download_s3_file(
                bucket_name,
                object_key,
                local_path,
            )

            df = pd.read_csv(local_path)

            print(
                f"Read {len(df)} rows from "
                f"s3://{bucket_name}/{object_key}"
            )

            df.to_sql(
                name=table_name,
                con=engine,
                schema="public",
                if_exists="append",
                index=False,
            )

            log_ingestion(
                engine=engine,
                file_name=file_name,
                file_path=f"s3://{bucket_name}/{object_key}",
                file_size=local_path.stat().st_size,
                row_count=len(df),
                status="SUCCESS",
                bucket_name=bucket_name,
                object_key=object_key,
                etag=etag,
            )

            print(
                f"Loaded {len(df)} rows "
                f"into public.{table_name}"
            )

            print("Ingestion status: SUCCESS")

        except Exception as e:
            log_ingestion(
                engine=engine,
                file_name=file_name,
                file_path=f"s3://{bucket_name}/{object_key}",
                file_size=(
                    local_path.stat().st_size
                    if local_path.exists()
                    else 0
                ),
                row_count=0,
                status="FAILED",
                error_message=str(e),
                bucket_name=bucket_name,
                object_key=object_key,
                etag=etag,
            )

            print(f"Ingestion failed: {e}")
            raise

if __name__ == "__main__":
    load_csv(
        "data/sample/orders_2026-09-17.csv",
        "raw_orders",
        bucket_name="sater-dagster-demo-20260910",
        object_key="raw/orders/orders_2026-09-17.csv",
        etag="abc123",
    )
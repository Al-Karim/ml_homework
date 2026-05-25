"""
ETL: PostgreSQL → MinIO (S3)
Reads all tables, converts to Parquet, uploads with date partitioning.
"""

import os
import io
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import create_engine
from minio import Minio
from minio.error import S3Error

# ── Connection settings ──────────────────────────────────────────────────────
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB   = os.getenv("PG_DB",   "oildb")
PG_USER = os.getenv("PG_USER", "pipeline_user")
PG_PASS = os.getenv("PG_PASS", "pipeline_pass")

MINIO_ENDPOINT  = os.getenv("MINIO_ENDPOINT",  "localhost:9000")
MINIO_ACCESS    = os.getenv("MINIO_ACCESS",     "minioadmin")
MINIO_SECRET    = os.getenv("MINIO_SECRET",     "minioadmin123")
MINIO_BUCKET    = os.getenv("MINIO_BUCKET",     "oil-pipeline")
MINIO_SECURE    = os.getenv("MINIO_SECURE",     "false").lower() == "true"

# Tables that have a date/timestamp column for partitioning
PARTITIONED_TABLES = {
    "production":     "date",
    "well_telemetry": "timestamp",
    "pump_sensors":   "timestamp",
    "deliveries":     "date",
    "well_targets":   "date",
}

# Tables without date partitioning (reference data)
REFERENCE_TABLES = [
    "wells", "pumps", "pump_failures",
    "drivers", "vehicles", "oil_stations",
]


def get_engine():
    url = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    return create_engine(url)


def get_minio_client():
    return Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS,
                 secret_key=MINIO_SECRET, secure=MINIO_SECURE)


def ensure_bucket(client: Minio, bucket: str):
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"  Created bucket: {bucket}")
    else:
        print(f"  Bucket exists: {bucket}")


def df_to_parquet_bytes(df: pd.DataFrame) -> bytes:
    table = pa.Table.from_pandas(df, preserve_index=False)
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    return buf.read()


def upload_bytes(client: Minio, bucket: str, object_name: str, data: bytes):
    client.put_object(
        bucket, object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type="application/octet-stream",
    )
    print(f"    Uploaded → s3://{bucket}/{object_name}  ({len(data):,} bytes)")


def extract_reference_table(engine, client: Minio, table: str):
    print(f"\n[REF] {table}")
    df = pd.read_sql(f"SELECT * FROM {table}", engine)
    print(f"  Rows: {len(df)}")
    data = df_to_parquet_bytes(df)
    upload_bytes(client, MINIO_BUCKET, f"raw/{table}/{table}.parquet", data)


def extract_partitioned_table(engine, client: Minio, table: str, date_col: str):
    print(f"\n[ETL] {table}  (partitioned by {date_col})")
    df = pd.read_sql(f"SELECT * FROM {table}", engine)
    print(f"  Total rows: {len(df)}")

    if df.empty:
        print("  Empty table, skipping.")
        return

    # Normalize date column to date only (strip time from timestamp)
    df["_part_date"] = pd.to_datetime(df[date_col]).dt.date

    for part_date, group in df.groupby("_part_date"):
        group = group.drop(columns=["_part_date"])
        year, month, day = str(part_date).split("-")
        object_name = f"raw/{table}/year={year}/month={month}/day={day}/data.parquet"
        data = df_to_parquet_bytes(group)
        upload_bytes(client, MINIO_BUCKET, object_name, data)

    print(f"  Partitions written: {df['_part_date'].nunique()}")


def run_etl():
    print("=" * 60)
    print("ETL: PostgreSQL → MinIO")
    print("=" * 60)

    engine = get_engine()
    client = get_minio_client()
    ensure_bucket(client, MINIO_BUCKET)

    # Reference tables
    for table in REFERENCE_TABLES:
        extract_reference_table(engine, client, table)

    # Partitioned tables
    for table, date_col in PARTITIONED_TABLES.items():
        extract_partitioned_table(engine, client, table, date_col)

    print("\n" + "=" * 60)
    print("ETL complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_etl()

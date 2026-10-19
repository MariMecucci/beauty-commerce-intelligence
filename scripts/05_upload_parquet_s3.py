
"""Envia arquivos Parquet para o armazenamento S3 local."""

import hashlib
import os
from pathlib import Path

import boto3
from botocore.config import Config
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BUCKET = "beauty-commerce"
ENDPOINT = "http://127.0.0.1:8333"

TABLES = {
    "silver": (
        "customers",
        "products",
        "orders",
        "order_items",
    ),
    "gold": (
        "monthly_sales",
        "top_products",
    ),
}


def main():
    access_key = os.getenv("S3_ACCESS_KEY_ID")
    secret_key = os.getenv("S3_SECRET_ACCESS_KEY")

    if not access_key or not secret_key:
        raise RuntimeError("Credenciais locais nao encontradas.")

    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}),
    )

    s3.head_bucket(Bucket=BUCKET)

    files = [
        (layer, table, ROOT / "data" / "parquet" / layer / f"{table}.parquet")
        for layer, tables in TABLES.items()
        for table in tables
    ]

    missing = [str(path) for _, _, path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Arquivos Parquet ausentes:\n" + "\n".join(missing)
        )

    print("Iniciando upload para S3 local...\n")

    for layer, table, path in files:
        key = f"{layer}/{table}.parquet"
        content = path.read_bytes()

        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=content,
            ContentType="application/vnd.apache.parquet",
        )

        response = s3.get_object(Bucket=BUCKET, Key=key)
        downloaded = response["Body"].read()

        local_hash = hashlib.sha256(content).hexdigest()
        remote_hash = hashlib.sha256(downloaded).hexdigest()

        if local_hash != remote_hash:
            raise RuntimeError(f"Falha de integridade: {key}")

        print(f"OK | s3://{BUCKET}/{key}")

    print(f"\nUpload concluido: {len(files)} arquivos verificados.")


if __name__ == "__main__":
    main()

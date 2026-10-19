
"""Valida a conexão com o armazenamento S3 local."""

import os
from pathlib import Path

import boto3
from botocore.config import Config
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

access_key = os.getenv("S3_ACCESS_KEY_ID")
secret_key = os.getenv("S3_SECRET_ACCESS_KEY")

if not access_key or not secret_key:
    raise RuntimeError("Credenciais locais não encontradas no .env")

s3 = boto3.client(
    "s3",
    endpoint_url="http://127.0.0.1:8333",
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name="us-east-1",
    config=Config(s3={"addressing_style": "path"}),
)

bucket = "beauty-commerce"

s3.head_bucket(Bucket=bucket)

print("Conexão S3 estabelecida com sucesso!")
print(f"Bucket encontrado: {bucket}")
print("Endpoint: http://127.0.0.1:8333")

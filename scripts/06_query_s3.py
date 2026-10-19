
"""Consulta arquivos Parquet no S3 local usando DuckDB."""

import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def sql_string(value):
    """Escapa um valor para uso como literal SQL."""
    return "'" + value.replace("'", "''") + "'"


def main():
    access_key = os.getenv("S3_ACCESS_KEY_ID")
    secret_key = os.getenv("S3_SECRET_ACCESS_KEY")

    if not access_key or not secret_key:
        raise RuntimeError("Credenciais S3 ausentes no .env")

    with duckdb.connect(":memory:") as conn:
        try:
            conn.execute("LOAD httpfs")
        except duckdb.Error:
            conn.execute("INSTALL httpfs")
            conn.execute("LOAD httpfs")

        conn.execute(f"""
            CREATE SECRET beauty_local (
                TYPE s3,
                PROVIDER config,
                KEY_ID {sql_string(access_key)},
                SECRET {sql_string(secret_key)},
                REGION 'us-east-1',
                ENDPOINT '127.0.0.1:8333',
                URL_STYLE 'path',
                USE_SSL false,
                SCOPE 's3://beauty-commerce'
            )
        """)

        query = """
            SELECT
                COUNT(*) AS total_registros,
                SUM(revenue_brl_cents) AS receita_centavos
            FROM read_parquet(?)
        """

        remote = conn.execute(
            query,
            ["s3://beauty-commerce/gold/monthly_sales.parquet"]
        ).fetchone()

        local_path = ROOT / "data/parquet/gold/monthly_sales.parquet"

        local = conn.execute(
            query,
            [str(local_path)]
        ).fetchone()

        if remote != local:
            raise RuntimeError(
                f"Resultados divergentes: S3={remote}, local={local}"
            )

        print("Consulta SQL no S3 local executada!")
        print(f"Registros: {remote[0]}")
        print(f"Receita: R$ {remote[1] / 100:,.2f}")
        print("Validacao: S3 e Parquet local consistentes.")


if __name__ == "__main__":
    main()

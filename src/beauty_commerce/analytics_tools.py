
"""Ferramentas SQL seguras para o Beauty Analytics AI Agent."""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "data" / "parquet" / "gold"


def parquet_path(table):
    allowed = {"monthly_sales", "top_products"}

    if table not in allowed:
        raise ValueError("Tabela não autorizada.")

    path = GOLD / f"{table}.parquet"

    if not path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    return str(path)


def sales_overview():
    """Retorna receita total e quantidade de meses analisados."""

    with duckdb.connect(":memory:") as db:
        revenue, months = db.execute(
            """
            SELECT
                COALESCE(SUM(revenue_brl_cents), 0),
                COUNT(DISTINCT sale_month)
            FROM read_parquet(?)
            """,
            [parquet_path("monthly_sales")],
        ).fetchone()

    return {
        "revenue_brl": revenue / 100,
        "months_analyzed": months,
        "currency": "BRL",
        "data_type": "synthetic",
    }


def top_brands(limit=5):
    """Retorna as marcas com maior faturamento."""

    if not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ValueError("O limite deve estar entre 1 e 10.")

    with duckdb.connect(":memory:") as db:
        rows = db.execute(
            """
            SELECT
                brand,
                SUM(revenue_brl_cents) AS revenue_cents
            FROM read_parquet(?)
            GROUP BY brand
            ORDER BY revenue_cents DESC, brand
            LIMIT ?
            """,
            [parquet_path("monthly_sales"), limit],
        ).fetchall()

    return [
        {"brand": brand, "revenue_brl": cents / 100}
        for brand, cents in rows
    ]


def top_products(limit=5):
    """Retorna os produtos com maior receita acumulada."""

    if not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ValueError("O limite deve estar entre 1 e 10.")

    with duckdb.connect(":memory:") as db:
        rows = db.execute(
            """
            SELECT
                product_name,
                brand,
                SUM(revenue_brl_cents) AS revenue_cents
            FROM read_parquet(?)
            GROUP BY product_id, product_name, brand
            ORDER BY revenue_cents DESC, product_name
            LIMIT ?
            """,
            [parquet_path("top_products"), limit],
        ).fetchall()

    return [
        {
            "product": name,
            "brand": brand,
            "revenue_brl": cents / 100,
        }
        for name, brand, cents in rows
    ]

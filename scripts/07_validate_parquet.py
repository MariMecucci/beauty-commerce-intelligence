
"""Valida integridade e reconciliacao dos datasets Parquet."""

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "parquet"

TABLES = {
    "silver_customers": ("silver/customers.parquet", ["customer_id"]),
    "silver_products": ("silver/products.parquet", ["product_id"]),
    "silver_orders": ("silver/orders.parquet", ["order_id"]),
    "silver_order_items": ("silver/order_items.parquet", ["order_item_id"]),
    "gold_monthly_sales": (
        "gold/monthly_sales.parquet",
        ["sale_month", "category", "brand"],
    ),
    "gold_top_products": (
        "gold/top_products.parquet",
        ["sale_month", "product_id"],
    ),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    report = json.loads(
        (ROOT / "reports" / "data_quality.json").read_text(
            encoding="utf-8"
        )
    )

    with duckdb.connect(":memory:") as db:
        for table, (relative_path, keys) in TABLES.items():
            path = DATA / relative_path
            require(path.is_file(), f"Arquivo ausente: {relative_path}")

            safe_path = path.resolve().as_posix().replace("'", "''")
            db.execute(
                f"CREATE TEMP VIEW {table} AS "
                f"SELECT * FROM read_parquet('{safe_path}')"
            )

            columns = {
                row[0] for row in db.execute(
                    f"DESCRIBE SELECT * FROM {table}"
                ).fetchall()
            }
            require(set(keys).issubset(columns), f"Schema invalido: {table}")

            count = db.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            require(count > 0, f"Tabela vazia: {table}")

            group_keys = ", ".join(keys)
            duplicates = db.execute(
                f"SELECT COUNT(*) FROM ("
                f"SELECT {group_keys} FROM {table} "
                f"GROUP BY {group_keys} HAVING COUNT(*) > 1)"
            ).fetchone()[0]
            require(duplicates == 0, f"Chaves duplicadas: {table}")

            null_condition = " OR ".join(f"{k} IS NULL" for k in keys)
            nulls = db.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {null_condition}"
            ).fetchone()[0]
            require(nulls == 0, f"Chaves nulas: {table}")

            source_name = table.removeprefix("silver_")
            if table.startswith("silver_"):
                expected_count = report["row_counts"][source_name]
                require(count == expected_count, f"Contagem invalida: {table}")

            print(f"OK | {table}: {count} registros")

        # Integridade referencial entre tabelas Silver
        checks = {
            "orders_customers": """
                SELECT COUNT(*) FROM silver_orders o
                LEFT JOIN silver_customers c
                ON o.customer_id = c.customer_id
                WHERE c.customer_id IS NULL
            """,
            "items_orders": """
                SELECT COUNT(*) FROM silver_order_items i
                LEFT JOIN silver_orders o
                ON i.order_id = o.order_id
                WHERE o.order_id IS NULL
            """,
            "items_products": """
                SELECT COUNT(*) FROM silver_order_items i
                LEFT JOIN silver_products p
                ON i.product_id = p.product_id
                WHERE p.product_id IS NULL
            """,
        }

        for name, query in checks.items():
            invalid = db.execute(query).fetchone()[0]
            require(invalid == 0, f"Referencia invalida: {name}")
            print(f"OK | integridade: {name}")

        # Reconciliacao da receita entre Silver, Gold e relatorio
        silver_revenue = db.execute("""
            SELECT COALESCE(SUM(i.quantity * i.unit_price_cents), 0)
            FROM silver_order_items i
            JOIN silver_orders o ON i.order_id = o.order_id
            WHERE o.status = 'completed'
        """).fetchone()[0]

        gold_revenue = db.execute("""
            SELECT COALESCE(SUM(revenue_brl_cents), 0)
            FROM gold_monthly_sales
        """).fetchone()[0]

        ranking_revenue = db.execute("""
            SELECT COALESCE(SUM(revenue_brl_cents), 0)
            FROM gold_top_products
        """).fetchone()[0]

        expected = report["revenue_brl_cents_completed_orders"]

        require(
            silver_revenue == gold_revenue == ranking_revenue == expected,
            "Receita divergente entre Silver, Gold e relatorio",
        )

        print("OK | Receita reconciliada entre Silver e Gold")
        print("Validacao de integridade concluida com sucesso!")


if __name__ == "__main__":
    main()

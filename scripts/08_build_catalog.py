
"""Gera um catalogo local de metadados para os datasets Parquet."""

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]

DATASETS = {
    "silver": {
        "customers": {
            "description": "Synthetic customer records by Brazilian state.",
            "keys": ["customer_id"],
            "upstream": ["raw/customers.csv"],
        },
        "products": {
            "description": "Beauty product catalog and listed prices.",
            "keys": ["product_id"],
            "upstream": ["raw/products.csv"],
        },
        "orders": {
            "description": "Customer orders and transaction status.",
            "keys": ["order_id"],
            "upstream": ["raw/orders.csv"],
        },
        "order_items": {
            "description": "Products, quantities and prices per order.",
            "keys": ["order_item_id"],
            "upstream": ["raw/order_items.csv"],
        },
    },
    "gold": {
        "monthly_sales": {
            "description": "Monthly revenue by category and brand.",
            "keys": ["sale_month", "category", "brand"],
            "upstream": [
                "silver/orders",
                "silver/order_items",
                "silver/products",
            ],
        },
        "top_products": {
            "description": "Monthly product revenue rankings.",
            "keys": ["sale_month", "product_id"],
            "upstream": [
                "silver/orders",
                "silver/order_items",
                "silver/products",
            ],
        },
    },
}


def main():
    catalog = {
        "project": "Beauty Commerce Intelligence",
        "domain": "Beauty Commerce",
        "environment": "local",
        "classification": "synthetic",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "datasets": [],
    }

    with duckdb.connect(":memory:") as db:
        for layer, tables in DATASETS.items():
            for name, metadata in tables.items():
                path = ROOT / "data" / "parquet" / layer / f"{name}.parquet"

                if not path.is_file():
                    raise FileNotFoundError(f"Dataset not found: {path}")

                cursor = db.execute(
                    "SELECT * FROM read_parquet(?) LIMIT 0",
                    [str(path)],
                )

                columns = [
                    {"name": item[0], "type": str(item[1])}
                    for item in cursor.description
                ]

                column_names = {item["name"] for item in columns}
                if not set(metadata["keys"]).issubset(column_names):
                    raise ValueError(f"Missing catalog keys: {layer}/{name}")

                count = db.execute(
                    "SELECT COUNT(*) FROM read_parquet(?)",
                    [str(path)],
                ).fetchone()[0]

                if count == 0:
                    raise ValueError(f"Empty dataset: {layer}/{name}")

                catalog["datasets"].append({
                    "name": name,
                    "layer": layer,
                    "description": metadata["description"],
                    "format": "parquet",
                    "classification": "synthetic",
                    "record_count": count,
                    "primary_key": metadata["keys"],
                    "columns": columns,
                    "upstream": metadata["upstream"],
                    "local_path": f"data/parquet/{layer}/{name}.parquet",
                    "object_key": f"{layer}/{name}.parquet",
                    "freshness_sla": "not_defined",
                })

                print(f"OK | {layer}/{name}: cataloged")

    output = ROOT / "reports" / "data_catalog.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"\nCatalog generated: {output}")
    print(f"Datasets: {len(catalog['datasets'])}")


if __name__ == "__main__":
    main()

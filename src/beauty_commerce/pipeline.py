"""Pipeline local Bronze → Silver → Gold com SQL + verificações de qualidade."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED = ("customers", "products", "orders", "order_items")
FIELDS = {
    "customers": ("customer_id", "state", "created_at"),
    "products": ("product_id", "brand", "product_name", "category", "list_price_cents"),
    "orders": ("order_id", "customer_id", "order_date", "status"),
    "order_items": ("order_item_id", "order_id", "product_id", "quantity", "unit_price_cents"),
}


class DataQualityError(ValueError):
    """Falha no contrato de dados (a execução é interrompida)."""


def _load_raw(folder: Path, entity: str) -> list[dict[str, str]]:
    path = folder / f"{entity}.csv"
    if not path.exists():
        raise DataQualityError(f"Fonte não encontrada: {path}")
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or not set(FIELDS[entity]) <= set(reader.fieldnames):
            raise DataQualityError(f"Schema incompatível em {path}")
        rows = list(reader)
    if not rows:
        raise DataQualityError(f"Fonte vazia: {path}")
    return rows


def _unique(rows: list[dict], key: str) -> None:
    keys = [row[key] for row in rows]
    if not all(keys) or len(keys) != len(set(keys)):
        raise DataQualityError(f"Chave nula ou duplicada: {key}")


def validate_contract(rows: dict[str, list[dict]]) -> dict[str, int]:
    _unique(rows["customers"], "customer_id")
    _unique(rows["products"], "product_id")
    _unique(rows["orders"], "order_id")
    _unique(rows["order_items"], "order_item_id")
    customer_ids = {r["customer_id"] for r in rows["customers"]}
    product_ids = {r["product_id"] for r in rows["products"]}
    order_ids = {r["order_id"] for r in rows["orders"]}
    for r in rows["products"]:
        if not r["brand"].strip() or not r["category"].strip() or int(r["list_price_cents"]) < 0:
            raise DataQualityError(f"Produto inválido: {r['product_id']}")
    for r in rows["orders"]:
        if r["customer_id"] not in customer_ids or r["status"] not in ("completed", "cancelled", "refunded"):
            raise DataQualityError(f"Pedido inválido: {r['order_id']}")
        try:
            from datetime import date
            date.fromisoformat(r["order_date"])
        except ValueError as error:
            raise DataQualityError(f"Data inválida no pedido {r['order_id']}") from error
    for r in rows["order_items"]:
        if (r["order_id"] not in order_ids or r["product_id"] not in product_ids
                or int(r["quantity"]) <= 0 or int(r["unit_price_cents"]) < 0):
            raise DataQualityError(f"Item inválido: {r['order_item_id']}")
    return {name: len(value) for name, value in rows.items()}


def _write_csv(path: Path, rows: list[dict], fieldnames: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fetch_dicts(db: sqlite3.Connection, statement: str) -> tuple[list[dict], tuple[str, ...]]:
    cursor = db.execute(statement)
    headers = tuple(column[0] for column in cursor.description)
    return [dict(zip(headers, row)) for row in cursor.fetchall()], headers


def run_pipeline(base_dir: Path) -> dict:
    """Valida todo o lote e gera Bronze, Silver, Gold e relatório de qualidade."""
    base_dir = Path(base_dir)
    data_dir = base_dir / "data"
    rows = {entity: _load_raw(data_dir / "raw", entity) for entity in REQUIRED}
    counts = validate_contract(rows)  # impede gerar saídas a partir de um lote inválido

    # Bronze: cópia fiel da entrada com checksum para demonstrar rastreabilidade.
    checksums = {}
    for entity in REQUIRED:
        original = data_dir / "raw" / f"{entity}.csv"
        destination = data_dir / "bronze" / original.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, destination)
        checksums[entity] = hashlib.sha256(destination.read_bytes()).hexdigest()

    db = sqlite3.connect(":memory:")
    try:
        schema = (REPO_ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
        db.executescript(schema)
        for r in rows["customers"]:
            db.execute("INSERT INTO customers VALUES (?, ?, ?)",
                       (r["customer_id"], r["state"].strip().upper(), r["created_at"]))
        for r in rows["products"]:
            db.execute("INSERT INTO products VALUES (?, ?, ?, ?, ?)",
                       (r["product_id"], r["brand"].strip(), r["product_name"].strip(),
                        r["category"].strip(), int(r["list_price_cents"])))
        for r in rows["orders"]:
            db.execute("INSERT INTO orders VALUES (?, ?, ?, ?)",
                       (r["order_id"], r["customer_id"], r["order_date"], r["status"]))
        for r in rows["order_items"]:
            db.execute("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)",
                       (r["order_item_id"], r["order_id"], r["product_id"],
                        int(r["quantity"]), int(r["unit_price_cents"])))
        db.commit()
        for entity in REQUIRED:
            silver_rows, headers = _fetch_dicts(db, f"SELECT * FROM {entity}")
            _write_csv(data_dir / "silver" / f"{entity}.csv", silver_rows, headers)

        gold_specs = {
            "monthly_sales": "gold_monthly_sales.sql",
            "top_products": "gold_top_products.sql",
        }
        gold_counts = {}
        for name, sql_file in gold_specs.items():
            statement = (REPO_ROOT / "sql" / sql_file).read_text(encoding="utf-8")
            gold_rows, headers = _fetch_dicts(db, statement)
            _write_csv(data_dir / "gold" / f"{name}.csv", gold_rows, headers)
            gold_counts[name] = len(gold_rows)

        revenue_cents = db.execute("""
            SELECT COALESCE(SUM(i.quantity * i.unit_price_cents), 0)
            FROM order_items i JOIN orders o ON o.order_id=i.order_id
            WHERE o.status='completed'
        """).fetchone()[0]
        completed_count = db.execute("SELECT COUNT(*) FROM orders WHERE status='completed'").fetchone()[0]
    finally:
        db.close()

    report = {
        "dataset_type": "synthetic",
        "contract_status": "passed",
        "row_counts": counts,
        "gold_row_counts": gold_counts,
        "completed_orders": completed_count,
        "revenue_brl_cents_completed_orders": revenue_cents,
        "bronze_sha256": checksums,
        "business_rule": "revenue excludes cancelled and refunded orders; shipping not modeled",
    }
    report_path = base_dir / "reports" / "data_quality.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report

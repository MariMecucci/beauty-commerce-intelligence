"""Gerador determinístico de dados SINTÉTICOS de comércio de cosméticos."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import random

BRANDS = ("Haru Glow", "Seoul Bloom", "Mira Skin", "Velvet Lab")
CATEGORIES = ("Skincare", "Makeup", "Haircare", "Bodycare")
REGIONS = ("SP", "RJ", "MG", "PR", "BA", "RS")
PRODUCT_NAMES = ("Serum", "Cleanser", "Toner", "Cream", "Mask", "Oil")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_dataset(base_dir: Path, *, seed: int = 42, n_orders: int = 500) -> dict[str, int]:
    """Cria quatro CSVs em data/raw. Nenhum dado representa pessoas reais."""
    if n_orders < 1:
        raise ValueError("n_orders deve ser maior que zero")
    rng = random.Random(seed)
    raw = Path(base_dir) / "data" / "raw"

    customers = [
        {"customer_id": f"C{i:04d}", "state": rng.choice(REGIONS),
         "created_at": (date(2025, 10, 1) + timedelta(days=rng.randrange(90))).isoformat()}
        for i in range(1, 81)
    ]
    products = []
    for i in range(1, 25):
        price = rng.randrange(3500, 22001, 500)
        products.append({
            "product_id": f"P{i:03d}", "brand": BRANDS[(i - 1) % len(BRANDS)],
            "product_name": f"{PRODUCT_NAMES[(i - 1) % len(PRODUCT_NAMES)]} {i:02d}",
            "category": CATEGORIES[((i - 1) // 3) % len(CATEGORIES)],
            "list_price_cents": price,
        })

    orders, items = [], []
    item_number = 0
    for n in range(1, n_orders + 1):
        order_id = f"O{n:06d}"
        status = rng.choices(("completed", "cancelled", "refunded"), (87, 8, 5))[0]
        orders.append({
            "order_id": order_id,
            "customer_id": rng.choice(customers)["customer_id"],
            "order_date": (date(2026, 1, 1) + timedelta(days=rng.randrange(273))).isoformat(),
            "status": status,
        })
        for product in rng.sample(products, k=rng.randint(1, 4)):
            item_number += 1
            items.append({
                "order_item_id": f"I{item_number:07d}",
                "order_id": order_id,
                "product_id": product["product_id"],
                "quantity": rng.randint(1, 3),
                "unit_price_cents": product["list_price_cents"],
            })

    _write_csv(raw / "customers.csv", list(customers[0]), customers)
    _write_csv(raw / "products.csv", list(products[0]), products)
    _write_csv(raw / "orders.csv", list(orders[0]), orders)
    _write_csv(raw / "order_items.csv", list(items[0]), items)
    return {"customers": len(customers), "products": len(products),
            "orders": len(orders), "order_items": len(items)}


"""Testes automatizados das ferramentas SQL do agente."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from beauty_commerce import analytics_tools


class AnalyticsToolsTests(unittest.TestCase):

    def setUp(self):
        """Cria dados Parquet isolados para os testes."""

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)

        self.gold = Path(temporary.name)

        with duckdb.connect(":memory:") as db:

            monthly_path = (
                self.gold / "monthly_sales.parquet"
            ).as_posix().replace("'", "''")

            db.execute(f"""
                COPY (
                    SELECT * FROM (VALUES
                        ('2026-01', 'Skincare', 'Velvet Lab', 125000),
                        ('2026-02', 'Makeup', 'Velvet Lab', 40000),
                        ('2026-02', 'Skincare', 'Haru Glow', 60000)
                    ) AS t(
                        sale_month,
                        category,
                        brand,
                        revenue_brl_cents
                    )
                ) TO '{monthly_path}' (FORMAT PARQUET)
            """)

            products_path = (
                self.gold / "top_products.parquet"
            ).as_posix().replace("'", "''")

            db.execute(f"""
                COPY (
                    SELECT * FROM (VALUES
                        (18, 'Oil 18', 'Seoul Bloom', 90000),
                        (12, 'Oil 12', 'Velvet Lab', 70000),
                        (21, 'Toner 21', 'Haru Glow', 30000)
                    ) AS t(
                        product_id,
                        product_name,
                        brand,
                        revenue_brl_cents
                    )
                ) TO '{products_path}' (FORMAT PARQUET)
            """)

        # Redireciona as ferramentas para os dados temporarios.
        patcher = patch.object(
            analytics_tools,
            "GOLD",
            self.gold,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_sales_overview(self):
        result = analytics_tools.sales_overview()

        self.assertEqual(result["revenue_brl"], 2250.0)
        self.assertEqual(result["months_analyzed"], 2)
        self.assertEqual(result["currency"], "BRL")
        self.assertEqual(result["data_type"], "synthetic")

    def test_top_brands(self):
        result = analytics_tools.top_brands(2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["brand"], "Velvet Lab")
        self.assertEqual(result[0]["revenue_brl"], 1650.0)
        self.assertEqual(result[1]["brand"], "Haru Glow")
        self.assertEqual(result[1]["revenue_brl"], 600.0)

    def test_top_products(self):
        result = analytics_tools.top_products(2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["product"], "Oil 18")
        self.assertEqual(result[0]["revenue_brl"], 900.0)
        self.assertEqual(result[1]["product"], "Oil 12")
        self.assertEqual(result[1]["revenue_brl"], 700.0)

    def test_invalid_limits(self):
        for function in (
            analytics_tools.top_brands,
            analytics_tools.top_products,
        ):
            for invalid in (0, 11, -1, "3", 2.5):
                with self.subTest(
                    function=function.__name__,
                    limit=invalid,
                ):
                    with self.assertRaises(ValueError):
                        function(invalid)

    def test_unauthorized_table(self):
        with self.assertRaises(ValueError):
            analytics_tools.parquet_path("orders")

    def test_missing_parquet(self):
        path = self.gold / "monthly_sales.parquet"
        path.unlink()

        with self.assertRaises(FileNotFoundError):
            analytics_tools.sales_overview()


if __name__ == "__main__":
    unittest.main()

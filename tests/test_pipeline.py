import csv
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from beauty_commerce.generator import generate_dataset
from beauty_commerce.pipeline import DataQualityError, run_pipeline


def load_csv(path):
    with path.open(newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))


class PipelineTest(unittest.TestCase):
    def test_generates_expected_files_and_gold_revenue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            counts = generate_dataset(root, seed=42, n_orders=40)
            report = run_pipeline(root)
            self.assertEqual(counts['orders'], 40)
            self.assertEqual(report['contract_status'], 'passed')
            self.assertTrue((root / 'data/gold/monthly_sales.csv').is_file())
            self.assertTrue((root / 'data/gold/top_products.csv').is_file())
            self.assertEqual(
                sum(int(r['revenue_brl_cents']) for r in load_csv(root / 'data/gold/monthly_sales.csv')),
                report['revenue_brl_cents_completed_orders'],
            )
            self.assertEqual(
                report['completed_orders'],
                sum(r['status'] == 'completed' for r in load_csv(root / 'data/raw/orders.csv')),
            )

    def test_rejects_invalid_product_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generate_dataset(root, n_orders=5)
            path = root / 'data/raw/order_items.csv'
            rows = load_csv(path)
            rows[0]['product_id'] = 'P999'
            with path.open('w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(DataQualityError):
                run_pipeline(root)
            self.assertFalse((root / 'data/gold/monthly_sales.csv').exists())

    def test_generator_is_reproducible(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            generate_dataset(Path(a), seed=13, n_orders=12)
            generate_dataset(Path(b), seed=13, n_orders=12)
            self.assertEqual(
                (Path(a) / 'data/raw/orders.csv').read_bytes(),
                (Path(b) / 'data/raw/orders.csv').read_bytes(),
            )

if __name__ == '__main__':
    unittest.main()

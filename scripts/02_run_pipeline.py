from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from beauty_commerce.pipeline import run_pipeline

if __name__ == '__main__':
    result = run_pipeline(ROOT)
    print(json.dumps({
        'quality': result['contract_status'],
        'completed_orders': result['completed_orders'],
        'revenue_brl': result['revenue_brl_cents_completed_orders'] / 100,
        'gold_row_counts': result['gold_row_counts'],
    }, indent=2))
    print('Arquivos em data/gold/ e reports/data_quality.json')

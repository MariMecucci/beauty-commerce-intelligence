from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from beauty_commerce.generator import generate_dataset

if __name__ == '__main__':
    counts = generate_dataset(ROOT)
    print('Dados sintéticos gerados com sucesso:', counts)

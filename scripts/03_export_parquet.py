r"""Exporta as camadas Silver e Gold do Beauty Commerce para Apache Parquet.

Pré-requisitos:
    py -3 scripts/01_generate_data.py
    py -3 scripts/02_run_pipeline.py
    .\.venv\Scripts\python.exe -m pip install duckdb

Execução (Windows):
    .\.venv\Scripts\python.exe scripts/03_export_parquet.py
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    "silver": ("customers", "products", "orders", "order_items"),
    "gold": ("monthly_sales", "top_products"),
}


def sql_file_path(path: Path) -> str:
    """Converte um caminho local em um literal SQL seguro para o DuckDB."""
    return "'" + path.resolve().as_posix().replace("'", "''") + "'"


def main() -> None:
    expected_inputs = [
        ROOT / "data" / layer / f"{table}.csv"
        for layer, tables in TABLES.items()
        for table in tables
    ]
    missing = [str(path) for path in expected_inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "CSV(s) ausente(s). Execute 01_generate_data.py e 02_run_pipeline.py primeiro:\n"
            + "\n".join(missing)
        )

    with duckdb.connect(database=":memory:") as conn:
        for layer, tables in TABLES.items():
            for table in tables:
                source = ROOT / "data" / layer / f"{table}.csv"
                target = ROOT / "data" / "parquet" / layer / f"{table}.parquet"
                target.parent.mkdir(parents=True, exist_ok=True)

                source_literal = sql_file_path(source)
                target_literal = sql_file_path(target)
                source_query = f"SELECT * FROM read_csv_auto({source_literal}, HEADER = TRUE)"
                before = conn.execute(f"SELECT COUNT(*) FROM ({source_query})").fetchone()[0]

                # Reexecutável: substitui somente a saída gerada por este script.
                target.unlink(missing_ok=True)
                conn.execute(
                    f"COPY ({source_query}) TO {target_literal} "
                    "(FORMAT PARQUET, COMPRESSION ZSTD)"
                )
                after = conn.execute(
                    f"SELECT COUNT(*) FROM read_parquet({target_literal})"
                ).fetchone()[0]
                if before != after:
                    raise RuntimeError(f"Contagem divergente em {table}: CSV={before}, Parquet={after}")
                print(f"OK | {layer}/{table}: {before} linhas -> {target.relative_to(ROOT)}")

    print("Exportação concluída: 6 arquivos Parquet gerados e contagens verificadas.")


if __name__ == "__main__":
    main()

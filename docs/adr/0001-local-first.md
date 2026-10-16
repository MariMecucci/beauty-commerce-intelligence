# ADR-0001: Local-first sem despesas obrigatórias

- **Status:** Aceito para a fase 1.
- **Contexto:** O projeto servirá como portfólio verificável, sem dependência de crédito AWS ou API paga.
- **Decisão:** Iniciar com CSV, SQLite (biblioteca padrão do Python), transformações SQL e unittest.
- **Por que:** Permite exercitar modelagem, contratos, tratamento de erros e regras de negócio com um setup quase instantâneo no Windows.
- **Trade-off:** Não é uma stack de produção em nuvem; CSV/SQLite não demonstram, por si sós, processamento distribuído, Airflow ou Athena.
- **Evolução planejada:** trocar os conectores por MySQL/MongoDB, gravar Parquet com DuckDB/PyArrow, orquestrar via Airflow, publicar no S3 e consultar no Athena.

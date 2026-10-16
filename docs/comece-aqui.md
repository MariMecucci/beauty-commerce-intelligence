# Guia em português — primeira execução

## Pré-requisito
- Python 3.11 ou superior
- VS Code (recomendado)
- Git, apenas quando for publicar no GitHub

Não precisa de Docker, conta AWS, cartão de crédito nem chave de API nesta primeira etapa.

## No Windows (PowerShell)
1. Descompacte e abra a pasta `beauty-commerce-intelligence` no VS Code.
2. Abra **Terminal → New Terminal**.
3. Execute:

```powershell
py -3 scripts/01_generate_data.py
py -3 scripts/02_run_pipeline.py
py -3 -m unittest discover -s tests -v
```

Se `py` não funcionar, troque por `python`.

## O que conferir
- `data/raw/`: quatro arquivos CSV que simulam fontes de vendas e produtos.
- `data/bronze/`: cópias fiéis dos arquivos de entrada.
- `data/silver/`: tabelas limpas, tipadas e verificadas.
- `data/gold/monthly_sales.csv`: receita por mês, marca e categoria.
- `data/gold/top_products.csv`: produtos ranqueados com `DENSE_RANK()`.
- `reports/data_quality.json`: evidências das verificações e checksum do Bronze.

## Como ler receita
- Valores monetários são armazenados em **centavos** para evitar erros de arredondamento.
- `revenue_brl_cents = 15990` significa R$ 159,90.
- Apenas pedidos `completed` contribuem para receita. `cancelled` e `refunded` são excluídos.

## Próxima etapa
- Adicionar MySQL para pedidos e MongoDB para produtos, via Docker Compose, mantendo os mesmos testes.
- Depois migrar Bronze/Silver/Gold para Parquet, introduzir Airflow e publicar o data lake em S3.

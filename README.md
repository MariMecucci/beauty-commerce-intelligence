# Beauty Commerce Intelligence

[![CI - Data Engineering](https://github.com/MariMecucci/beauty-commerce-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/MariMecucci/beauty-commerce-intelligence/actions/workflows/ci.yml)

**Data Engineering · Medallion Architecture · SQL · DuckDB · Parquet · S3-compatible storage · Streamlit · Qwen3 · LangGraph**

An end-to-end, **local-first data engineering and analytical AI portfolio project** for a fictional beauty and K-beauty retailer. The solution generates reproducible synthetic commerce data, validates and transforms it through Bronze/Silver/Gold layers, stores analytics-ready Parquet datasets, and exposes approved business metrics to a locally hosted AI agent.

> **Project status (October 2026):** A local Bronze/Silver/Gold data pipeline, Parquet export, S3-compatible object storage integration, data quality and metadata checks, CI, a Qwen3 4B tool-calling agent, and the **interactive Streamlit dashboard (BCI V5.2)** are implemented. The dashboard and agent were tested locally; GitHub Actions covers the deterministic data pipeline and 15 unit tests, **not** the Ollama runtime or interactive UI. AWS-managed services, Airflow, MySQL, and MongoDB are **not implemented**. All brands, customers, products, and financial figures are synthetic.

### Application preview

![Beauty Commerce Intelligence: interactive executive dashboard](docs/images/dashboard-overview.png)

*Executive Overview — validated synthetic Gold Parquet data, brand rankings, filtered KPIs, and descriptive insights. The screenshots are from local runs; no public hosted application is implied.*

## 1. Business problem and use cases

A fictional cosmetics retailer wants consistent answers to commercial questions without relying on unverified spreadsheet calculations or LLM-generated financial figures:

- What is total completed-order revenue, and how many sales months are represented?
- Which beauty brands generate the highest revenue?
- Which products rank highest by accumulated revenue?
- Can the analytical datasets be reproduced, audited for quality, and reconciled across storage formats?
- Can an AI assistant select **approved analytical tools** without receiving unrestricted SQL or file-system access?

### Reproducible sample results

| Metric | Sample result |
|---|---:|
| Customers | 80 |
| Products | 24 |
| Orders | 500 |
| Order items | 1,267 |
| Months represented in Gold sales | 9 |
| Total completed-order revenue | BRL 281,550.00 |

These figures are from the project's deterministic **synthetic demonstration dataset**, not a real business. Re-running the generator with different parameters can change the results.

## 2. Architecture

```mermaid
flowchart TD
    A[Synthetic customers, products, orders, items] --> B[Raw CSV]
    B --> C[Bronze snapshots and checksums]
    C --> D[Silver validation and relational transformations]
    D --> E[Gold SQL: monthly sales and product rankings]
    D --> F[Silver CSV datasets]
    E --> G[Gold CSV datasets]
    F --> H[DuckDB Parquet export]
    G --> H
    H --> I[Local Silver and Gold Parquet]
    I --> J[boto3 upload and hash verification]
    J --> K[SeaweedFS local S3-compatible bucket]
    K --> L[DuckDB httpfs S3 queries]
    I --> M[DuckDB local reconciliation]
    L --> N[Compare local and S3 aggregates]
    M --> N
    I --> O[Approved DuckDB analytics functions]
    P[Business question] --> Q[Ollama Qwen3 4B and LangGraph]
    Q --> R[Allowlisted tool calls]
    R --> O
    O --> S[Validated structured tool results]
    S --> T[Python formatting and source attribution]
    I --> U[Metadata catalog and integrity checks]
    D --> V[Data-quality report]
    I --> W[Streamlit BCI Dashboard]
    W --> Q
    T --> W
    U --> W
    V --> W
```

**Important boundaries:** The AI agent reads the **local Gold Parquet files** through approved Python/DuckDB functions; it does not query SeaweedFS directly. SeaweedFS is a local implementation of S3-compatible object-storage APIs, **not** a deployment of Amazon S3, AWS Glue, or Athena.

## 3. Technology stack and implementation status

| Component | Technology | Status |
|---|---|---|
| Synthetic ingestion and transformations | Python, SQL, SQLite | Implemented |
| Medallion data model | Raw / Bronze / Silver / Gold | Implemented |
| Columnar analytics | DuckDB, Apache Parquet | Implemented |
| Local object storage | Docker Compose, SeaweedFS, boto3 | Implemented and tested locally |
| Data quality and metadata | SQL checks, reconciliation, JSON catalog, `unittest` | Implemented |
| CI/CD | GitHub Actions on Ubuntu | Implemented |
| Local LLM inference | Ollama, Qwen3 4B | Implemented and tested locally |
| AI tool routing | LangGraph, LangChain `ChatOllama`, approved Python tools | Implemented and tested locally |
| Production cloud platform | AWS S3, Glue, Athena, IAM | Not implemented |
| Additional databases | MySQL, MongoDB | Planned |
| Orchestration / monitoring | Apache Airflow, freshness checks, SLAs | Planned |
| Analytical UI | Streamlit, pandas, custom CSS, DuckDB | Implemented and manually tested locally (V5.2) |
| Local agent evaluation | Six scenarios using Qwen3 4B and tool calls | Implemented and run locally; not part of CI |

## 4. Data products

| Dataset | Layer | Purpose |
|---|---|---|
| `customers`, `products`, `orders`, `order_items` | Raw / Bronze / Silver | Generated entities and validated records |
| `monthly_sales` | Gold | Completed-order revenue by month, brand, and category |
| `top_products` | Gold | Product revenue and monthly rankings |
| `reports/data_quality.json` | Quality | Contract results, counts, and related checks |
| `reports/data_catalog.json` | Metadata | Local catalog with dataset schemas, keys, upstream sources, and row counts |

Monetary source fields use **integer BRL cents**. The displayed agent responses convert amounts to BRL. Cancelled and refunded orders are excluded from completed-order revenue; shipping is not modeled.

The project generates six local Parquet datasets: four Silver entities plus `gold/monthly_sales.parquet` and `gold/top_products.parquet`.

## 5. AI agent: design and behavior

The **Beauty Analytics AI Agent** is a tool-calling application, not a free-form text-to-SQL agent. A local Qwen3 4B model interprets the question, and a LangGraph workflow routes it to one of three approved tools:

| Approved tool | Data source | Output |
|---|---|---|
| `get_sales_overview` | `gold/monthly_sales.parquet` | Revenue, months represented |
| `get_top_brands` | `gold/monthly_sales.parquet` | Revenue ranking by brand |
| `get_top_products` | `gold/top_products.parquet` | Accumulated revenue ranking by product |

The tools use parameterized, predefined read-only DuckDB queries and a table allowlist. Tool arguments for rankings are constrained to an integer limit from 1 to 10. The graph stops after the tool step, and Python formats the returned values rather than displaying an unverified LLM-written financial answer.

### Implemented safeguards

- No general-purpose SQL execution is exposed to the model.
- Only the three explicitly registered analytics tools can be called through the graph.
- The data functions restrict Parquet access to the two expected Gold datasets.
- A lightweight deterministic policy rejects several common **forecasting** requests before model invocation.
- No commercial result is displayed when the model invokes no approved tool.
- The interface labels all results as synthetic and names the source dataset.

**Local evaluation:** `scripts/11_evaluate_agent.py` evaluates six cases (revenue, brand ranking, product ranking, unsupported forecast, unsupported profit, and one prompt-injection attempt). The observed local run passed **6/6**. This is a small functional sample, not a robust security or statistical benchmark.

**Limitations:** Keyword-based forecast detection is incomplete and can miss paraphrases or misclassify requests. Tool-routing behavior is model-dependent. The project is **not a production-grade authorization layer, prompt-injection defense, forecast engine, or fully evaluated agent**. Additional adversarial tests, schema validation, logging, and failure handling are on the roadmap.

## 6. Interactive dashboard — Beauty Intelligence Platform

The **BCI V5.2** interface is a local Streamlit application with an original, beauty-inspired design system (warm ivory, plum, muted rose). It is an analytical product rather than a hosted public service.

| Area | Implemented behavior |
|---|---|
| **Overview** | Total revenue, months covered, leading brand/product, monthly revenue, brand contribution, and descriptive insights. |
| **Brands** | Revenue ranking, revenue share, category ranking, and tabular detail. |
| **Products** | Top product revenue comparison and a detailed table. |
| **AI Studio** | A natural-language question form, Qwen3/LangGraph tool selection, Python-rendered financial results with source attribution, and supported refusal behavior. |
| **Data Trust** | Selected-slice Gold revenue reconciliation, Gold dataset inventory, and availability indicators for local quality/catalog/agent-evaluation reports. |

**Filters:** The dashboard supports period, brand, and category multi-selects. These filter the **Overview, Brands, Products, and reconciliation display**. The **AI Studio intentionally uses the complete local Gold dataset**, irrespective of dashboard filters, and tells the user so in the interface. This scope difference should not be confused with a bug or a filtered answer.

**Data provenance:** Charts and KPIs read `data/parquet/gold/monthly_sales.parquet` and `data/parquet/gold/top_products.parquet`. The local model chooses among three approved functions; monetary figures are read from DuckDB tool results rather than free-form model text. The current Data Trust tab reports file availability, but it is **not** a substitute for inspecting the full JSON report contents or running the validation scripts.

![Beauty AI Studio: local Qwen3 agent returning grounded brand rankings](docs/images/ai-studio.png)

*AI Studio — approved `get_top_brands` tool returning ranked synthetic brands. The model requires a separate, locally running Ollama service.*

### Run the dashboard on Windows

After following the data-generation instructions in the setup section below, install the UI and AI dependencies in the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install streamlit pandas langgraph langchain-ollama
```

For standalone commercial analytics and visuals, Ollama is not required. To query the AI Studio, install and start Ollama separately and download `qwen3:4b` as described below.

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\dashboard\app.py --server.address 127.0.0.1
```

Open the **Local URL** printed in the terminal (typically `http://127.0.0.1:8501`; another port may be selected if it is occupied). The `.streamlit/config.toml` file supplies the brand color theme; no hosted service or AWS account is required.

### Locally validated UI scenarios

- Full dataset: BRL 281,550.00 of completed-order revenue across nine months.
- Brand-only filter for **Velvet Lab**: BRL 81,710.00; the leading product changes to **Oil 12**.
- AI Studio: total revenue, top brands, and top products returned via approved tools.
- Unsupported future revenue forecast: the UI displayed the implemented policy refusal.

These are observed outcomes of the synthetic demonstration data; they do not constitute automated Streamlit regression tests. Live UI rendering, Ollama connectivity, and adversarial robustness are **not** yet tested in GitHub Actions.

## 7. Repository guide

```text
beauty-commerce-intelligence/
├── .github/workflows/ci.yml
├── .streamlit/config.toml            # BCI theme; no secrets
├── dashboard/app.py                  # Local interactive Streamlit app
├── compose.yaml
├── data/                         # Generated datasets; ignored by Git
│   ├── raw/  bronze/  silver/  gold/
│   └── parquet/silver/  parquet/gold/
├── docs/
│   ├── adr/0001-local-first.md
│   └── images/                        # UI screenshots referenced in README
│       ├── dashboard-overview.png
│       └── ai-studio.png
├── reports/                      # Generated local reports; ignored by Git
├── scripts/
│   ├── 01_generate_data.py
│   ├── 02_run_pipeline.py
│   ├── 03_export_parquet.py
│   ├── 04_validate_s3.py
│   ├── 05_upload_parquet_s3.py
│   ├── 06_query_s3.py
│   ├── 07_validate_parquet.py
│   ├── 08_build_catalog.py
│   ├── 09_test_ollama_python.py
│   ├── 10_beauty_agent.py
│   └── 11_evaluate_agent.py
├── sql/                          # Data model SQL definitions
├── src/beauty_commerce/
│   ├── generator.py
│   ├── pipeline.py
│   ├── analytics_tools.py
│   └── agent_policy.py
├── tests/
│   ├── test_pipeline.py
│   ├── test_analytics_tools.py
│   └── test_agent_policy.py
├── .gitignore
└── README.md
```

## 8. Local setup — Windows PowerShell

Prerequisites: Windows with Python 3.11+ and sufficient free disk space. Docker Desktop is only required for the **optional** S3-compatible storage section. Ollama is only required to run the **AI agent**. This project does not require an AWS account or paid inference API.

From the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install duckdb==1.5.6 boto3 python-dotenv langgraph langchain-ollama
```

### Generate the data lake locally

```powershell
.\.venv\Scripts\python.exe .\scripts\01_generate_data.py
.\.venv\Scripts\python.exe .\scripts\02_run_pipeline.py
.\.venv\Scripts\python.exe .\scripts\03_export_parquet.py
.\.venv\Scripts\python.exe .\scripts\07_validate_parquet.py
.\.venv\Scripts\python.exe .\scripts\08_build_catalog.py
```

For the Streamlit UI, also install `streamlit` and `pandas` (see [Interactive dashboard](#6-interactive-dashboard--beauty-intelligence-platform)).

The generator uses a reproducible seed by default. Generated data and reports are not tracked in Git; reproduce them locally before running the AI agent.

### Run all automated tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The current test suite contains **15 unit tests** across pipeline behavior, SQL analytics functions, and lightweight forecast-policy checks. Tests use isolated synthetic fixtures where appropriate and do not require an Ollama model download. The dashboard does not have an automated visual regression test in this suite.

### Run the local model evaluation (optional)

After the Gold datasets are generated and Ollama is running with `qwen3:4b`:

```powershell
.\.venv\Scripts\python.exe -u .\scripts\11_evaluate_agent.py
```

This executes six model-assisted cases and writes a local `reports/agent_evaluation.json` report. Unlike `unittest`, these checks require the local model and are not in GitHub Actions.

### Run the local AI agent

Install [Ollama for Windows](https://ollama.com/download/windows), ensure its local server is running, then download the model:

```powershell
ollama pull qwen3:4b
ollama list
```

The Ollama service must be reachable at `http://127.0.0.1:11434`. On supported hardware the model may run on a GPU; CPU inference may be slower. The model download uses local disk space.

Try the approved questions:

```powershell
.\.venv\Scripts\python.exe -u .\scripts\10_beauty_agent.py "Qual foi o faturamento total?"
.\.venv\Scripts\python.exe -u .\scripts\10_beauty_agent.py "Quais sao as 3 marcas com maior faturamento?"
.\.venv\Scripts\python.exe -u .\scripts\10_beauty_agent.py "Quais sao os 3 produtos com maior faturamento acumulado?"
```

Try an unsupported forecast question:

```powershell
.\.venv\Scripts\python.exe -u .\scripts\10_beauty_agent.py "Qual sera o faturamento da empresa no proximo ano?"
```

The last example is handled by the deterministic policy; it does not produce a fabricated revenue forecast. A basic Ollama/Python connectivity check is available in `scripts/09_test_ollama_python.py`.

## 9. Optional local S3-compatible storage

Create a `.env` file in the repository root with local development-only credentials:

```dotenv
S3_ACCESS_KEY_ID=beauty_local
S3_SECRET_ACCESS_KEY=replace_with_a_strong_local_dev_secret
```

Never commit `.env`, share credentials in screenshots, or reuse personal passwords. The Docker Compose file binds the demonstration endpoint to `127.0.0.1:8333`.

```powershell
docker compose config --quiet
docker compose up -d
.\.venv\Scripts\python.exe .\scripts\04_validate_s3.py
.\.venv\Scripts\python.exe .\scripts\05_upload_parquet_s3.py
.\.venv\Scripts\python.exe .\scripts\06_query_s3.py
```

The workflow uploads the six Silver/Gold Parquet objects, verifies hashes and queries an object through DuckDB `httpfs`, comparing a revenue aggregate with the local data. To stop containers without deleting the persistent volume:

```powershell
docker compose down
```

The `s3://beauty-commerce/...` keys refer to the **private local SeaweedFS bucket**, not public Amazon S3 resources.

## 10. Data quality, metadata and CI

Implemented checks include required fields, valid values, identifiers, referential relationships, Bronze SHA-256 snapshots, Parquet row counts, Gold revenue reconciliation, and a local JSON dataset catalog with upstream lineage hints.

The [CI workflow](.github/workflows/ci.yml) runs on pushes and pull requests using Python 3.11 on Ubuntu. It executes:

1. The Python `unittest` suite (pipeline, analytics, agent-policy tests).
2. Synthetic CSV generation and the transformation pipeline.
3. Silver/Gold export to Parquet.
4. Parquet schema and revenue reconciliation checks.
5. Parquet integrity checks and metadata catalog validation.

**CI does not currently run the Ollama/Qwen3 model, the Streamlit UI, or the Docker/SeaweedFS integration.** Manual model-routing checks are not equivalent to automated end-to-end agent evaluations. See the [workflow history](https://github.com/MariMecucci/beauty-commerce-intelligence/actions) for execution results.

## 11. Architectural decisions and trade-offs

- **Local-first design:** No mandatory cloud account or paid API; a free-to-run learning environment with ordinary computer/electricity/internet costs.
- **Medallion layers:** Separate raw inputs, validation, and consumer-ready Gold outputs.
- **Parquet + DuckDB:** Efficient columnar analytics on a laptop without a managed cloud warehouse.
- **S3-compatible storage:** Practice object-storage APIs without claiming AWS-managed infrastructure expertise.
- **Tool calling instead of unrestricted SQL:** Narrower surface area for errors and unauthorized data access, at the cost of limited question coverage.
- **Deterministic formatting:** Commercial figures come directly from query results, not unconstrained model prose.
- **Tests without local LLM dependency:** Fast CI checks cover deterministic components; model-level evaluation runs separately.
- **Purpose-built interface:** Streamlit provides reproducible interactive analysis on a laptop while custom styling communicates a consistent beauty-industry identity; it is not a production deployed SaaS.
- **Clear filtering boundary:** Dashboard commercial views honor period/brand/category filters, but AI Studio intentionally queries the full approved Gold data, as disclosed in the UI.

See [ADR-0001: Local-first](docs/adr/0001-local-first.md) for the initial architectural rationale.

## 12. Roadmap

- [x] Synthetic ingestion and Bronze/Silver/Gold processing.
- [x] DuckDB/Parquet datasets and SQL revenue models.
- [x] S3-compatible object storage locally with SeaweedFS.
- [x] Data quality, metadata catalog, and GitHub Actions validation.
- [x] Local Qwen3 4B tool-calling agent with three approved SQL-backed analytics tools.
- [x] Initial forecasting refusal rules and unit tests.
- [x] Initial six-case local agent evaluation script; 6/6 observed in one run.
- [x] Local Streamlit BCI V5.2 dashboard with filtered analytics, AI Studio, and Data Trust view.
- [ ] Broader agent evaluation: paraphrases, repeated-run routing, unsupported intents, prompt-injection cases, and failure paths.
- [ ] Robust policy, structured validation, and improved audit logs.
- [ ] MySQL and MongoDB connectors, incremental ingestion, and idempotent loads.
- [ ] Apache Airflow orchestration, monitoring, freshness checks, and defined SLAs.
- [ ] Optional AWS deployment design after a dedicated cost/security assessment.

## 13. Portfolio scope

This is an **educational and technical portfolio prototype**, not a production deployment or an actual cosmetics company's financial system. The Streamlit dashboard is run locally and is not publicly hosted. It demonstrates data modeling, architectural trade-offs, automated validation, local object-storage integration, and constrained AI tool calling with synthetic data. Future integrations are described as planned, not delivered.

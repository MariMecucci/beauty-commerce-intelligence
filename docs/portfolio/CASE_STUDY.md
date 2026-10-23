# Beauty Commerce Intelligence | Technical case study

**An end-to-end data engineering and local AI analytics prototype for a fictional beauty and K-beauty retailer.**

**Roles demonstrated:** Data Engineer · Analytics Engineer · AI Engineer (prototype)
**Tech:** Python, SQL, SQLite, DuckDB, Apache Parquet, Docker Compose, SeaweedFS, boto3, Streamlit, LangGraph, Ollama/Qwen3, GitHub Actions.
**Repository:** https://github.com/MariMecucci/beauty-commerce-intelligence

![Architecture overview](assets/architecture-overview.png)

## 1. The business problem

A fictional beauty retailer needed a reproducible way to answer: **How much revenue did completed orders generate, which brands and products performed best, and can every number be traced back to validated datasets?** The brief deliberately uses *synthetic* data, so the solution can be inspected without exposing customer records or requiring a paid cloud account.

## 2. What I built

- Generated deterministic commerce entities and transformed them through **Raw → Bronze → Silver → Gold** layers using Python and SQL.
- Exported analytics-ready **Parquet** data and validated schemas, relationships, row counts and Gold revenue reconciliation.
- Exercised **S3-compatible APIs locally** with SeaweedFS, boto3, SHA-256 verification and DuckDB HTTPFS queries. This is **not AWS-managed S3, Glue or Athena**.
- Built a **Streamlit analytics interface** with filters for month, brand and category, descriptive insights, brand/product rankings, and a Data Trust view.
- Connected a **local Qwen3 4B + LangGraph** agent to **three allowlisted DuckDB analytics tools**. The model selects a tool; Python renders the tool's structured results rather than trusting LLM-written revenue figures.
- Added **15 unit tests** and GitHub Actions checks for deterministic pipeline generation, Parquet integrity, revenue reconciliation and metadata catalog validation.

## 3. Reproducible demonstration results

| Measure | Example value |
|---|---:|
| Synthetic customers | 80 |
| Synthetic products | 24 |
| Orders | 500 |
| Order items | 1,267 |
| Gold sales months | 9 |
| Completed-order revenue | BRL 281,550.00 |
| Unit tests | 15 passing in the validated run |

These are **fictional, generated** outcomes, not actual sales, growth, revenue impact or a real client result. Data may differ if generator inputs change.

## 4. Product demonstration

![Streamlit executive overview](../images/dashboard-overview.png)

*The Overview displays validated Gold metrics, trend charts, filtered brand ranking and descriptive insights.*

![AI Studio tool-backed result](../images/ai-studio.png)

*The AI Studio accepts a business question, routes it to an approved analytical function and displays sourced, structured results. It does not inherit the Overview filters.*

### Verified example interactions

| Question | Controlled behavior |
|---|---|
| What was total completed-order revenue? | `get_sales_overview` → BRL 281,550.00 / 9 months |
| Which three brands had the highest revenue? | `get_top_brands` → a source-labeled ranking |
| Which products lead revenue? | `get_top_products` → a source-labeled ranking |
| What will next year's revenue be? | The implemented scope policy refuses to forecast |

## 5. Technical reasoning — not just a dashboard

1. **Local-first:** optimized for low-cost reproducibility; accepts the absence of managed-cloud operations and production scaling.
2. **Medallion structure:** isolates raw snapshots, validated entities and consumer-ready aggregates.
3. **DuckDB + Parquet:** analytical queries on a laptop without running a permanent warehouse; does not simulate distributed processing.
4. **Narrow AI tools:** avoids unrestricted model-generated SQL and generates numbers from validated tools, but supports only a constrained set of questions.
5. **Separate deterministic CI:** fast tests and schema/reconciliation checks run without an LLM; live Ollama and Streamlit are verified manually.

Read the details: [Architecture](architecture-overview.md) · [Engineering decisions](engineering-decisions.md) · [Product showcase](product-showcase.md).

## 6. Current limits and next technical investments

- Not publicly hosted; running the demo requires a local environment, generated Parquet files and Ollama for the AI Studio.
- No AWS-managed services, Airflow orchestration, MySQL or MongoDB connectors, forecasting engine or production authorization system.
- The agent's forecast refusals are keyword-based; additional adversarial evaluation, logging and structured validation are planned.
- Next engineering priority: reproducible packaging, stronger agent/Streamlit tests, improved data freshness checks and more robust error handling **before** broadening cloud services.

## 7. Why this case matters

The project demonstrates a full line of reasoning from **business requirement → data model → quality contract → analytical consumption → AI tool boundary → observable result**, with explicit evidence and clear limits. It is intended as a technical portfolio and discussion artifact for data-platform and analytics-engineering work — not a claim of commercial production deployment.

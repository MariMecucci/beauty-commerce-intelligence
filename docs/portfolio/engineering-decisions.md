# Engineering decisions | Trade-offs and evidence

Decisions below reflect the current [implementation](https://github.com/MariMecucci/beauty-commerce-intelligence), not aspirational features.

| Decision | Why it was appropriate | Cost / trade-off | Evidence in repo |
|---|---|---|---|
| Local-first prototype rather than managed AWS | Reproducible and inexpensive portfolio iteration | Doesn't prove AWS operations/IAM or production SLAs | [`docs/adr/0001-local-first.md`](../adr/0001-local-first.md), `compose.yaml` |
| Raw → Bronze → Silver → Gold | Creates distinct validation and consumption boundaries | More transformation stages than a simple CSV notebook | `src/beauty_commerce/pipeline.py`, `sql/` |
| Integer cents for BRL revenue | Avoids cumulative floating-point error in base models | Requires explicit conversion at display boundaries | `src/beauty_commerce/analytics_tools.py` |
| DuckDB + Parquet | Fast columnar reads and SQL aggregations without a warehouse server | Not a distributed processing framework | `scripts/03_export_parquet.py`, `src/beauty_commerce/analytics_tools.py` |
| SeaweedFS S3-compatible API | Demonstrates boto3, object keys and remote query patterns locally | Not equivalent to AWS S3 service management | `compose.yaml`, `scripts/04_validate_s3.py`, `05_upload_parquet_s3.py`, `06_query_s3.py` |
| Tool-call restrictions for local AI | Grounds money values in approved SQL and limits model authority | Only three question families; imperfect intent policy | `scripts/10_beauty_agent.py`, `src/beauty_commerce/agent_policy.py` |
| Separate tests and CI | Deterministic checks run quickly, without Qwen3 | CI does not cover runtime inference or browser UX | `.github/workflows/ci.yml`, `tests/` |
| Streamlit + CSS styling | Easy demonstration of business semantics and premium UI | Styling is coupled to Streamlit; mobile/responsive refinements remain | `dashboard/app.py`, `.streamlit/config.toml` |

## Reliability safeguards demonstrated

- Contract checks for expected table columns, identifiers and relational integrity.
- SHA-256 Bronze snapshots and S3 upload verification.
- Cross-layer / local-vs-remote revenue reconciliation checks.
- Dataset metadata catalog with schema, source references and row counts.
- Three allowlisted AI analytical tools, limited integer ranking sizes, and tool-return validation before displaying results.
- Deterministic policy refusal of common unsupported forecasting intents.

## What is *not* proven

No public SLA, production deployment, cloud IAM, distributed load, operational orchestration, robust authentication/authorization, production-grade prompt-injection resistance, broad agent evaluation or live-LLM CI. A 15/15 unit-test run is evidence of its tested scope — **not** evidence of overall system security or production readiness.

## Next improvement priorities

1. Extract pure aggregation / filtering code from the Streamlit UI and create tests for empty selections and reconciliation mismatches.
2. Increase coverage for model tool routing: multiple phrasings, bad arguments, tool errors, timeouts and prompt-injection attempts.
3. Add structured request/response traces without recording secrets, plus model availability diagnostics.
4. Package setup reproducibly and document CPU/GPU memory requirements; evaluate a small hosted demo only after security and cost review.
5. If business requirements justify it, introduce incremental ingestion, orchestration/freshness monitoring and controlled cloud deployment.

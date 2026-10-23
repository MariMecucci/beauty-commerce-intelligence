# Product showcase | From technical pipeline to user experience

**The goal:** present complex engineering work through a usable commercial analytics interface, not a generic dashboard template.

## A. Executive Overview — business metrics that reconcile

![BCI executive overview](../images/dashboard-overview.png)

The Overview exposes completed-order revenue, the number of months represented, the leading brand and the leading product. It includes a monthly revenue trend, a revenue-by-brand comparison and descriptive highlights. Users filter by **month, brand and category**; revenue and leaders recalculate from validated local Gold Parquet data.

**Example:** selecting only fictional *Velvet Lab* across all periods and categories yields BRL 81,710.00 and selects *Oil 12* as the leading product in that slice. This was exercised manually in the Streamlit UI.

## B. AI Studio — approved questions, sourced answers

![BCI local AI Studio](../images/ai-studio.png)

AI Studio uses local **Ollama Qwen3 4B + LangGraph** for tool selection, then returns validated structured results from `get_sales_overview`, `get_top_brands`, or `get_top_products`. The response labels source Gold datasets; it does not use the model to fabricate currency amounts.

The model is a **constrained analytical router**, not a free-form SQL assistant or generalized forecasting engine. A future-revenue request is refused by the current scope rule. The AI Studio intentionally **does not share the commercial page filters**.

## C. Data Trust — an explicit trust surface

The Data Trust tab shows whether filtered Gold revenue reconciles and whether local quality/catalog/agent-evaluation JSON report files are present. The interface currently displays report *presence*, not a full interactive audit of every report assertion. This distinction matters in hiring conversations.

## D. UX choices

- **Visual language:** warm off-white, plum and dusty-rose contrast, generous whitespace and editorial headers inspired by contemporary beauty branding — not copied from another creator's website.
- **Analytical priority:** financial amounts shown with clear BRL formatting; branded visual elements are secondary to comparability and traceability.
- **Separation of concerns:** deterministic data/metrics remain independent from language-model narration.
- **Transparency:** synthetic-data notices, clearly stated local-only operation and stated AI limitations.

## Demo flow (90 seconds)

1. **00:00-00:15 — Problem:** show the Overview and explain why fragmented commerce metrics need validated transformations.
2. **00:15-00:35 — Filter:** select Velvet Lab; note the revenue and product leadership update.
3. **00:35-01:00 — AI Studio:** ask for top brands; show that one approved tool, not arbitrary SQL, produced the answer.
4. **01:00-01:15 — Trust:** show reconciliation and report presence in Data Trust.
5. **01:15-01:30 — Engineering:** show the architecture and CI, then state the local/S3-compatible and non-production boundaries.

**Demo environment:** local Windows/Streamlit; the repository does not currently provide a public interactive app. A screen recording is more accessible to recruiters who will not install Ollama.

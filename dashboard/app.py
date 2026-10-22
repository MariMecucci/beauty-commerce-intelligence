r"""BCI DASHBOARD V5.2 — polished brand rankings + interactive local AI Studio.

Beauty Commerce Intelligence — painel comercial local.

Iniciar na raiz do projeto:
    .\.venv\Scripts\python.exe -m streamlit run .\dashboard\app.py

Requer: streamlit, pandas e duckdb instalados no ambiente virtual.
"""

import json
from html import escape
from pathlib import Path
from runpy import run_path
import sys

import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
# Streamlit inicia a aplicacao fora do pacote src/. Garanta os imports locais.
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
GOLD = ROOT / "data" / "parquet" / "gold"
REPORTS = ROOT / "reports"

st.set_page_config(
    page_title="Beauty Commerce Intelligence | BCI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {background: #F8F6F3; color: #272127;}
    .block-container {max-width: 1510px; padding: 1.5rem clamp(1.2rem,2.8vw,3.3rem) 3.5rem;}
    [data-testid="stHeader"] {background: #F8F6F3;}
    .stApp h1, .stApp h2, .stApp h3 {color: #272127;}
    /* Explicit specificity: avoids Streamlit overriding the white hero title. */
    .stApp .bci-hero h1.bci-hero-title {color: #FFF9F5 !important;}
    .stApp .bci-hero h1.bci-hero-title em {color: #F2C8D7 !important;}
    .stApp .bci-hero .bci-hero-sub {color: #FBF0F3 !important;}
    .stApp .bci-hero .bci-overline {color: #F7CBD8 !important;}
    .bci-header {display:flex;align-items:center;justify-content:space-between;
      border-bottom:1px solid #DCD2CF;padding:8px 0 19px;gap:14px;flex-wrap:wrap;}
    .bci-monogram {font:700 2rem Georgia,serif;color:#603A4B;letter-spacing:-.065em;}
    .bci-brand {font:700 .7rem Arial,sans-serif;letter-spacing:.14em;color:#33262E;margin-left:15px;}
    .bci-meta {font:600 .65rem Arial,sans-serif;letter-spacing:.1em;color:#796E73;}
    .bci-hero {border-radius:19px;padding:48px 52px;margin:26px 0 22px;
      position:relative;overflow:hidden;
      box-shadow:0 20px 50px rgba(57,30,45,.10);
      background: radial-gradient(circle at 84% 49%,rgba(202,152,173,.24) 0%,transparent 32%),
      linear-gradient(115deg,#35232F 0%,#603A4B 62%,#845E71 100%);}
    .bci-hero:after {content:'01 / THE INTELLIGENCE EDIT';position:absolute;right:40px;
      bottom:24px;letter-spacing:.14em;color:#E7C3D0;font:600 .64rem Arial,sans-serif;}
    .bci-overline {font:700 .72rem Arial,sans-serif;letter-spacing:.18em;color:#E9C3D0;margin-bottom:13px;}
    .bci-hero-title {font:400 clamp(2.1rem,3.7vw,3.65rem)/1.14 Georgia,serif;
      color:#FFF9F5;margin:0 0 16px;max-width:780px;letter-spacing:-.025em;}
    .bci-hero-title em {color:#E9BDCE;}
    .bci-hero-sub {font:.92rem/1.65 Arial,sans-serif;color:#F1E5EA;max-width:600px;}
    .bci-heading {font:400 1.75rem Georgia,serif;color:#332B2E;
      margin:25px 0 12px;padding-bottom:9px;border-bottom:1px solid #DED6D2;}
    .bci-note {font:.79rem/1.6 Arial,sans-serif;color:#655B61;margin:9px 0 14px;}
    .bci-card {background:#FFFEFD;border:1px solid #E5D9D7;border-radius:14px;
      padding:22px;min-height:145px;box-shadow:0 6px 20px rgba(63,38,49,.035);}
    .bci-card:hover {border-color:#C4A9B4;box-shadow:0 10px 24px rgba(63,38,49,.075);}
    .bci-card-label {font:700 .69rem Arial,sans-serif;letter-spacing:.1em;color:#8F697B;}
    .bci-card-value {font:400 clamp(1.25rem,2vw,1.85rem) Georgia,serif;
      color:#603A4B;margin:10px 0;word-break:break-word;}
    .bci-card-foot {font:.72rem Arial,sans-serif;color:#82787A;}
    .bci-insight {background:#F0E9E7;border-top:2px solid #926479;
      border-radius:0 0 9px 9px;padding:18px;min-height:115px;
      font:400 1.06rem/1.45 Georgia,serif;color:#403039;}
    .bci-ai {background:#F2E9ED;border:1px solid #E3D3DC;border-radius:14px;padding:25px;}
    .bci-ai-response {background:#FFFEFD;border:1px solid #E5D9D7; border-radius:12px;padding:18px;}
    /* Horizontal comparisons with exact BRL labels, avoiding misleading numeric axes. */
    .bci-rank-card {padding:14px 17px 10px;background:#FFFEFD;border:1px solid #E5D9D7;
      border-radius:12px;min-height:315px;box-sizing:border-box;}
    .bci-rank-row {margin:0 0 20px;}
    .bci-rank-meta {display:flex;align-items:baseline;justify-content:space-between;
      gap:10px;margin-bottom:8px;font:600 .8rem Arial,sans-serif;color:#44343D;}
    .bci-rank-label {min-width:0;overflow-wrap:anywhere;}
    .bci-rank-value {white-space:nowrap;font-weight:700;color:#603A4B;font-variant-numeric:tabular-nums;}
    .bci-rank-track {width:100%;height:12px;border-radius:7px;background:#F2EBEB;overflow:hidden;}
    .bci-rank-fill {height:100%;border-radius:7px;background:linear-gradient(90deg,#603A4B,#A07A89);}
    .bci-footer {margin-top:38px;border-top:1px solid #DED6D2;padding-top:18px;
      font:600 .67rem Arial,sans-serif;letter-spacing:.1em;color:#8A7C81;}
    /* Better readability and responsive layouts, without changing Streamlit widgets. */
    [data-testid="stCaptionContainer"] p {color:#655B61; font-size:.79rem;}
    [data-testid="stExpander"] {border-radius:10px;border:1px solid #E1D5D3;}
    [data-testid="stTabs"] [data-baseweb="tab"] {font-weight:650;letter-spacing:.055em;}
    @media(max-width:720px) {
      .block-container{padding:1rem;}
      .bci-hero{padding:30px 23px 57px;}
      .bci-hero:after{left:23px;right:auto;bottom:19px;font-size:.56rem;}
      .bci-hero-title{font-size:2.25rem;}
      .bci-brand {display:block;margin-left:0;margin-top:1px;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def brl(value: float) -> str:
    return "R$ " + f"{float(value):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def show_card(label: str, value: str, footnote: str) -> None:
    st.markdown(
        '<div class="bci-card">'
        f'<div class="bci-card-label">{escape(label.upper())}</div>'
        f'<div class="bci-card-value">{escape(str(value))}</div>'
        f'<div class="bci-card-foot">{escape(footnote)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def read_parquet(file_name: str, modified_ns: int) -> pd.DataFrame:
    # Cache invalida automaticamente quando o Parquet for regenerado.
    path = GOLD / file_name
    with duckdb.connect(":memory:") as db:
        return db.execute("SELECT * FROM read_parquet(?)", [str(path)]).df()


def show_rank_bars(frame: pd.DataFrame, label_column: str, limit: int = 8) -> None:
    """Custom horizontal revenue bars with accessible labels and exact values.

    Does not depend on Streamlit's auto-formatted axis ticks.
    """
    if frame.empty:
        st.info("Nenhum dado disponível para esta comparação.")
        return
    sample = frame.head(limit)
    maximum = max(0.0, float(sample["revenue_brl"].max()))
    rows = []
    for _, item in sample.iterrows():
        value = float(item["revenue_brl"])
        proportion = max(0.0, min(100.0, value / maximum * 100.0)) if maximum > 0 else 0.0
        label = escape(str(item[label_column]))
        amount = escape(brl(value))
        rows.append(
            '<div class="bci-rank-row">'
            '<div class="bci-rank-meta">'
            f'<span class="bci-rank-label">{label}</span>'
            f'<strong class="bci-rank-value">{amount}</strong>'
            '</div>'
            '<div class="bci-rank-track" role="img" '
            f'aria-label="{label}: {amount}">'
            f'<div class="bci-rank-fill" style="width:{proportion:.2f}%"></div>'
            '</div></div>'
        )
    st.markdown(
        '<div class="bci-rank-card">' + ''.join(rows) + '</div>',
        unsafe_allow_html=True,
    )


def validate_frame(frame: pd.DataFrame, required: set, name: str) -> pd.DataFrame:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em {name}: {', '.join(sorted(missing))}")
    if frame.empty:
        raise ValueError(f"{name} está vazio")
    frame = frame.copy()
    for col in ("sale_month", "brand", "category"):
        if col in frame.columns:
            frame[col] = frame[col].astype(str)
    frame["revenue_brl_cents"] = pd.to_numeric(
        frame["revenue_brl_cents"], errors="raise"
    )
    if frame["revenue_brl_cents"].isna().any():
        raise ValueError(f"{name} contém receita nula")
    return frame


def aggregate_data(sales: pd.DataFrame, products: pd.DataFrame, months, brands, categories):
    sf = sales.loc[
        sales["sale_month"].isin(months)
        & sales["brand"].isin(brands)
        & sales["category"].isin(categories)
    ].copy()
    pf = products.loc[
        products["sale_month"].isin(months)
        & products["brand"].isin(brands)
        & products["category"].isin(categories)
    ].copy()
    if sf.empty or pf.empty:
        return None

    def agg(frame, keys):
        output = frame.groupby(keys, as_index=False)["revenue_brl_cents"].sum()
        output["revenue_brl"] = output["revenue_brl_cents"].astype(float) / 100.0
        return output

    monthly = agg(sf, ["sale_month"]).sort_values("sale_month")
    brand_rank = agg(sf, ["brand"]).sort_values("revenue_brl", ascending=False)
    category_rank = agg(sf, ["category"]).sort_values("revenue_brl", ascending=False)
    product_rank = agg(pf, ["product_id", "product_name", "brand"]).sort_values(
        "revenue_brl", ascending=False
    )
    total_cents = int(sf["revenue_brl_cents"].sum())
    product_cents = int(pf["revenue_brl_cents"].sum())
    return {
        "revenue": total_cents / 100.0,
        "months": monthly,
        "brands": brand_rank,
        "categories": category_rank,
        "products": product_rank,
        "reconciled": total_cents == product_cents,
    }


st.markdown(
    '<div class="bci-header"><div><span class="bci-monogram">BCI.</span>'
    '<span class="bci-brand">BEAUTY COMMERCE INTELLIGENCE</span></div>'
    '<span class="bci-meta">LOCAL ANALYTICS &nbsp; / &nbsp; V05.2 / SYNTHETIC DATA</span></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="bci-hero"><div class="bci-overline">BEAUTY INTELLIGENCE PLATFORM</div>'
    '<h1 class="bci-hero-title">Understand beauty <em>beyond the numbers.</em></h1>'
    '<div class="bci-hero-sub">Engenharia de dados, inteligência comercial e análise de beleza '
    'em uma experiência premium, reproduzível e local.</div></div>',
    unsafe_allow_html=True,
)

sales_path = GOLD / "monthly_sales.parquet"
products_path = GOLD / "top_products.parquet"
if not sales_path.is_file() or not products_path.is_file():
    st.error("Arquivos Gold não encontrados. Gere o pipeline antes de abrir o dashboard.")
    st.code(
        ".\\.venv\\Scripts\\python.exe .\\scripts\\01_generate_data.py\n"
        ".\\.venv\\Scripts\\python.exe .\\scripts\\02_run_pipeline.py\n"
        ".\\.venv\\Scripts\\python.exe .\\scripts\\03_export_parquet.py",
        language="powershell",
    )
    st.stop()

try:
    sales = validate_frame(
        read_parquet(sales_path.name, sales_path.stat().st_mtime_ns),
        {"sale_month", "brand", "category", "revenue_brl_cents"},
        "monthly_sales",
    )
    products = validate_frame(
        read_parquet(products_path.name, products_path.stat().st_mtime_ns),
        {"sale_month", "product_id", "product_name", "brand", "category", "revenue_brl_cents"},
        "top_products",
    )
except Exception as exc:
    st.error(f"Problema na leitura dos arquivos Gold: {exc}")
    st.stop()

with st.expander("Filtros · período, marca e categoria", expanded=False):
    c1, c2, c3 = st.columns(3)
    all_months = sorted(sales["sale_month"].unique().tolist())
    all_brands = sorted(sales["brand"].unique().tolist())
    all_categories = sorted(sales["category"].unique().tolist())
    with c1:
        sel_months = st.multiselect("Período", all_months, default=all_months)
    with c2:
        sel_brands = st.multiselect("Marcas", all_brands, default=all_brands)
    with c3:
        sel_categories = st.multiselect("Categorias", all_categories, default=all_categories)

model = aggregate_data(sales, products, sel_months, sel_brands, sel_categories)
if model is None:
    st.warning("Nenhuma venda corresponde aos filtros selecionados.")
    st.stop()

months = model["months"]
brands = model["brands"]
categories = model["categories"]
products_rank = model["products"]
revenue = model["revenue"]
period_count = len(months)
brand_name = str(brands.iloc[0]["brand"])
product_name = str(products_rank.iloc[0]["product_name"])

page_overview, page_brands, page_products, page_ai, page_quality = st.tabs(
    ["OVERVIEW", "BRANDS", "PRODUCTS", "AI STUDIO", "DATA TRUST"]
)

with page_overview:
    st.markdown('<div class="bci-heading">Executive overview</div>', unsafe_allow_html=True)
    st.caption("Uma leitura executiva do negócio fictício — métricas atualizadas pelos filtros acima.")
    for column, label, value, description in zip(
        st.columns(4),
        ["Receita total", "Meses analisados", "Marca líder", "Produto líder"],
        [brl(revenue), str(period_count), brand_name, product_name],
        ["Pedidos concluídos", "Meses no recorte", "Maior receita", "Maior receita"],
    ):
        with column:
            show_card(label, value, description)

    st.markdown('<div class="bci-heading">The revenue story</div>', unsafe_allow_html=True)
    st.caption("Tendência e composição do faturamento no período selecionado · R$.")
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        st.caption("Receita por mês (R$)")
        st.line_chart(
            months.set_index("sale_month")[["revenue_brl"]],
            color="#774759",
            height=320,
        )
    with right:
        st.caption("Receita por marca (R$) · valores absolutos")
        show_rank_bars(brands, "brand", limit=6)

    st.markdown('<div class="bci-heading">What the data says</div>', unsafe_allow_html=True)
    st.caption("Insights descritivos calculados com DuckDB/Parquet, sem previsões.")
    leader_share = float(brands.iloc[0]["revenue_brl"]) / revenue if revenue else 0
    category_share = float(categories.iloc[0]["revenue_brl"]) / revenue if revenue else 0
    messages = [
        f"{brand_name} representa {leader_share:.1%} da receita selecionada.",
        f"{categories.iloc[0]['category']} concentra {category_share:.1%} do faturamento.",
        f"Receita média mensal no recorte: {brl(revenue / period_count)}.",
    ]
    for column, message in zip(st.columns(3), messages):
        with column:
            st.markdown(
                f'<div class="bci-insight">{escape(message)}</div>',
                unsafe_allow_html=True,
            )

with page_brands:
    st.markdown('<div class="bci-heading">Brand performance</div>', unsafe_allow_html=True)
    show_rank_bars(brands, "brand", limit=10)
    table = brands[["brand", "revenue_brl"]].copy()
    table["participacao_pct"] = table["revenue_brl"] / revenue * 100
    st.dataframe(table, hide_index=True, width="stretch")
    st.subheader("Categorias")
    show_rank_bars(categories, "category", limit=10)

with page_products:
    st.markdown('<div class="bci-heading">Product intelligence</div>', unsafe_allow_html=True)
    top = products_rank.head(10)[["product_name", "brand", "revenue_brl"]].copy()
    st.bar_chart(
        top.set_index("product_name")[["revenue_brl"]],
        color="#774759",
        height=380,
    )
    st.dataframe(top, hide_index=True, width="stretch")
    st.caption("Não há previsão de vendas nem inventário/estoque implementados.")

# ============================================================
# AI STUDIO: lazy-loaded agent, no model required for other tabs
# ============================================================

@st.cache_resource(show_spinner=False)
def load_local_agent():
    # The existing script already registers the three approved SQL tools.
    # run_name prevents invoking its command-line main() entry point.
    module = run_path(
        str(ROOT / "scripts" / "10_beauty_agent.py"),
        run_name="bci_dashboard_agent_module",
    )
    return module["build_agent"](), module["SYSTEM_PROMPT"]


def ask_local_agent(question: str) -> dict:
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
    from beauty_commerce.agent_policy import is_forecast_question

    if is_forecast_question(question):
        return {
            "kind": "blocked",
            "message": "Ainda não há modelo de previsão de vendas implementado. "
                       "Consulte faturamento histórico, marcas ou produtos.",
        }

    graph, system_prompt = load_local_agent()
    result = graph.invoke(
        {"messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question + "\n/no_think"),
        ]},
        config={"recursion_limit": 6},
    )
    calls = [
        item for item in result["messages"]
        if isinstance(item, ToolMessage)
    ]
    if not calls:
        return {
            "kind": "unsupported",
            "message": "Nenhuma ferramenta analítica autorizada foi selecionada. "
                       "Tente perguntar por faturamento, marcas ou produtos.",
        }

    if len(calls) != 1:
        raise ValueError("O agente retornou um número inesperado de ferramentas.")

    msg = calls[0]
    sources = {
        "get_sales_overview": "Gold/monthly_sales.parquet",
        "get_top_brands": "Gold/monthly_sales.parquet",
        "get_top_products": "Gold/top_products.parquet",
    }
    if msg.name not in sources:
        raise ValueError("Ferramenta não autorizada retornada pelo agente.")
    if getattr(msg, "status", "success") == "error":
        raise RuntimeError("A consulta de dados falhou.")
    payload = json.loads(msg.content)

    # Validate the expected structure before presenting any commercial result.
    if msg.name == "get_sales_overview":
        if not isinstance(payload, dict) or not {
            "revenue_brl", "months_analyzed"
        }.issubset(payload):
            raise ValueError("Resposta inválida da ferramenta de faturamento.")
        float(payload["revenue_brl"])
        int(payload["months_analyzed"])
    else:
        if not isinstance(payload, list) or len(payload) > 10:
            raise ValueError("Ranking inválido retornado pela ferramenta.")
        expected = {"brand", "revenue_brl"} if msg.name == "get_top_brands" else {
            "product", "brand", "revenue_brl"
        }
        for item in payload:
            if not isinstance(item, dict) or not expected.issubset(item):
                raise ValueError("Formato inválido de uma linha do ranking.")
            float(item["revenue_brl"])
    return {
        "kind": "ok",
        "tool": msg.name,
        "source": sources[msg.name],
        "data": payload,
    }


def show_agent_answer(answer: dict) -> None:
    if answer["kind"] == "blocked":
        st.warning(answer["message"])
        return
    if answer["kind"] == "unsupported":
        st.info(answer["message"])
        return

    tool = answer["tool"]
    data = answer["data"]
    st.caption("Resposta baseada exclusivamente nos dados Gold validados")
    if tool == "get_sales_overview":
        c1, c2 = st.columns(2)
        c1.metric("Faturamento total", brl(data["revenue_brl"]))
        c2.metric("Meses analisados", int(data["months_analyzed"]))
    else:
        if not data:
            st.info("Nenhum registro retornado.")
        elif tool == "get_top_brands":
            st.subheader("Marcas com maior faturamento")
            table = pd.DataFrame([
                {"Marca": item["brand"], "Receita": brl(item["revenue_brl"])}
                for item in data
            ])
            st.dataframe(table, hide_index=True, width="stretch")
        else:
            st.subheader("Produtos com maior faturamento")
            table = pd.DataFrame([
                {"Produto": item["product"], "Marca": item["brand"],
                 "Receita": brl(item["revenue_brl"])}
                for item in data
            ])
            st.dataframe(table, hide_index=True, width="stretch")
    st.caption(f"Ferramenta: {tool} · Fonte: {answer['source']} · Dados sintéticos")


with page_ai:
    st.markdown('<div class="bci-heading">Beauty AI Studio</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="bci-ai"><h3>Ask better questions. Get grounded answers.</h3>'
        '<p>Qwen3 4B + LangGraph + ferramentas SQL aprovadas. A IA seleciona a ferramenta; '
        'os valores exibidos vêm diretamente do DuckDB, sem texto financeiro inventado.</p></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Consultas locais via Ollama · Requer o serviço em 127.0.0.1:11434 e o modelo qwen3:4b. "
        "O AI Studio consulta todo o dataset Gold e NÃO aplica os filtros da Overview."
    )
    with st.form("bci_ai_question_form", clear_on_submit=False):
        user_question = st.text_input(
            "Pergunte ao Beauty Analytics AI Agent",
            placeholder="Ex.: Quais são as três marcas com maior faturamento?",
        )
        submitted = st.form_submit_button("Consultar com IA", type="primary")
    st.caption(
        "Exemplos: 'Qual foi o faturamento total?' · "
        "'Quais são as 3 marcas com maior faturamento?' · "
        "'Quais são os 3 produtos mais vendidos em receita?'"
    )
    if submitted:
        if not user_question.strip():
            st.warning("Digite uma pergunta antes de consultar.")
        else:
            try:
                with st.spinner("O agente está consultando as ferramentas analíticas..."):
                    st.session_state["bci_ai_answer"] = ask_local_agent(user_question.strip())
                st.session_state["bci_ai_question"] = user_question.strip()
            except Exception as error:
                st.session_state.pop("bci_ai_answer", None)
                st.error("Não foi possível concluir a consulta local ao agente.")
                st.caption(
                    "Verifique se o Ollama está ativo, se qwen3:4b foi baixado e "
                    "se o ambiente tem langgraph e langchain-ollama instalados."
                )
                with st.expander("Detalhes técnicos"):
                    st.code(f"{type(error).__name__}: {error}")
    if "bci_ai_answer" in st.session_state:
        st.markdown('<div class="bci-heading">Result · Resposta validada</div>', unsafe_allow_html=True)
        st.caption(f"Pergunta: {st.session_state.get('bci_ai_question', '')}")
        show_agent_answer(st.session_state["bci_ai_answer"])

with page_quality:
    st.markdown('<div class="bci-heading">Data Trust Center</div>', unsafe_allow_html=True)
    if model["reconciled"]:
        st.success("Receita reconciliada entre os datasets Gold para os filtros atuais.")
    else:
        st.error("Receita divergente entre os datasets Gold. Verifique os dados antes de usar este recorte.")
    st.dataframe(
        pd.DataFrame([
            {"Dataset": "monthly_sales", "Camada": "Gold", "Formato": "Parquet"},
            {"Dataset": "top_products", "Camada": "Gold", "Formato": "Parquet"},
        ]),
        hide_index=True,
        width="stretch",
    )
    for label, filename in [
        ("Relatório de qualidade", "data_quality.json"),
        ("Catálogo de metadados", "data_catalog.json"),
        ("Avaliação do agente", "agent_evaluation.json"),
    ]:
        status = "encontrado" if (REPORTS / filename).is_file() else "não encontrado"
        st.caption(f"{label}: {status}")

st.markdown(
    '<div class="bci-footer">BCI. &nbsp; / &nbsp; LOCAL-FIRST DATA ENGINEERING '
    '& AI &nbsp; / &nbsp; COMMERCIAL DATA ARE SYNTHETIC</div>',
    unsafe_allow_html=True,
)


"""Beauty Analytics AI Agent — LangGraph + Ollama + DuckDB."""

import json
import sys
import unicodedata
from pathlib import Path

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from beauty_commerce.analytics_tools import (
    sales_overview,
    top_brands,
    top_products,
)


# ==========================================================
# 1. FERRAMENTAS SQL AUTORIZADAS
# ==========================================================

@tool
def get_sales_overview() -> str:
    """Consulta faturamento total e quantidade de meses analisados."""
    return json.dumps(sales_overview(), ensure_ascii=False)


@tool
def get_top_brands(limit: int = 3) -> str:
    """Consulta marcas com maior faturamento. Limite entre 1 e 10."""
    return json.dumps(top_brands(limit), ensure_ascii=False)


@tool
def get_top_products(limit: int = 3) -> str:
    """Consulta produtos com maior faturamento. Limite entre 1 e 10."""
    return json.dumps(top_products(limit), ensure_ascii=False)


TOOLS = [
    get_sales_overview,
    get_top_brands,
    get_top_products,
]


# ==========================================================
# 2. INSTRUCOES DO AGENTE
# ==========================================================

SYSTEM_PROMPT = """
Voce e o Beauty Analytics AI Agent, um agente especializado
em analise comercial de uma empresa ficticia de beleza.

Sua tarefa e selecionar ferramentas analiticas autorizadas.

Ferramentas disponiveis:
- Faturamento geral ou meses: get_sales_overview.
- Ranking de marcas: get_top_brands.
- Ranking de produtos: get_top_products.

Regras obrigatorias:
- Responda somente com base nos dados disponiveis.
- Para consultas comerciais, chame uma ferramenta.
- Nunca invente valores, marcas, produtos ou periodos.
- Nao execute SQL diretamente.
- Nao solicite acesso a arquivos ou sistemas externos.
- Os dados comerciais sao sinteticos.
- Nao apresente previsoes como resultados historicos.
- Se nenhuma ferramenta se aplicar, nao chame ferramentas.
"""


# ==========================================================
# 3. FORMATACAO DE VALORES
# ==========================================================

def format_brl(value):
    """Formata valores numericos como moeda brasileira."""

    text = f"{value:,.2f}"

    return (
        "R$ "
        + text.replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )


# ==========================================================
# 4. CONTROLE DE PERGUNTAS FORA DO ESCOPO
# ==========================================================

def normalize_text(text):
    """Remove acentos e padroniza o texto."""

    normalized = unicodedata.normalize(
        "NFKD",
        text.casefold(),
    )

    return "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )


def is_forecast_question(question: str) -> bool:
    """Identifica algumas solicitacoes de previsao nao suportadas."""

    normalized = normalize_text(question)

    unsupported_terms = (
        "proximo ano",
        "proximo mes",
        "ano que vem",
        "mes que vem",
        "previsao",
        "prever",
        "projecao",
        "projetar",
        "faturamento futuro",
        "vendas futuras",
        "vai faturar",
        "sera o faturamento",
        "quanto vendera",
    )

    return any(
        term in normalized
        for term in unsupported_terms
    )


# ==========================================================
# 5. CONSTRUCAO DO AGENTE LANGGRAPH
# ==========================================================

def build_agent():
    """Constroi o agente com acesso a ferramentas autorizadas."""

    model = ChatOllama(
        model="qwen3:4b",
        base_url="http://127.0.0.1:11434",
        temperature=0,
        reasoning=False,
        num_ctx=4096,
        num_predict=300,
    )

    model_with_tools = model.bind_tools(TOOLS)

    def assistant_node(state: MessagesState):
        response = model_with_tools.invoke(
            state["messages"]
        )

        return {"messages": [response]}

    graph = StateGraph(MessagesState)

    graph.add_node(
        "assistant",
        assistant_node,
    )

    graph.add_node(
        "tools",
        ToolNode(TOOLS),
    )

    graph.add_edge(
        START,
        "assistant",
    )

    graph.add_conditional_edges(
        "assistant",
        tools_condition,
    )

    # Encerrar apos executar as ferramentas.
    # Os resultados comerciais serao formatados pelo Python.
    graph.add_edge(
        "tools",
        END,
    )

    return graph.compile()


# ==========================================================
# 6. FORMATACAO DOS RESULTADOS SQL
# ==========================================================

def display_tool_results(tool_results):
    """Apresenta exclusivamente resultados das ferramentas."""

    print("\n=== FERRAMENTAS EXECUTADAS ===")

    for message in tool_results:
        print(f"- {message.name}")

        if getattr(message, "status", "success") == "error":
            raise RuntimeError(
                f"Falha na ferramenta: {message.name}"
            )

    print("\n=== RESPOSTA VALIDADA PELOS DADOS ===")

    for message in tool_results:
        data = json.loads(message.content)

        if message.name == "get_sales_overview":
            print(
                f"Faturamento total: "
                f"{format_brl(data['revenue_brl'])}"
            )

            print(
                f"Meses analisados: "
                f"{data['months_analyzed']}"
            )

            print("Fonte: Gold/monthly_sales")

        elif message.name == "get_top_brands":
            print("Marcas com maior faturamento:")

            for position, item in enumerate(data, 1):
                print(
                    f"{position}. {item['brand']} - "
                    f"{format_brl(item['revenue_brl'])}"
                )

            print("Fonte: Gold/monthly_sales")

        elif message.name == "get_top_products":
            print("Produtos com maior faturamento:")

            for position, item in enumerate(data, 1):
                print(
                    f"{position}. {item['product']} "
                    f"({item['brand']}) - "
                    f"{format_brl(item['revenue_brl'])}"
                )

            print("Fonte: Gold/top_products")

        else:
            raise RuntimeError(
                f"Ferramenta inesperada: {message.name}"
            )


# ==========================================================
# 7. EXECUCAO PRINCIPAL
# ==========================================================

def main():
    question = (
        " ".join(sys.argv[1:]).strip()
        or "Qual foi o faturamento total e quantos meses foram analisados?"
    )

    print("\n=== BEAUTY ANALYTICS AI AGENT ===")
    print(f"Pergunta: {question}")

    # Bloqueio deterministico de algumas perguntas fora do escopo.
    if is_forecast_question(question):
        print("\n=== PERGUNTA FORA DO ESCOPO ===")

        print(
            "Ainda nao tenho um modelo de previsao de vendas "
            "implementado. Posso consultar o faturamento "
            "historico, as marcas e os produtos mais rentaveis."
        )

        return

    print("\nConsultando ferramentas...")

    agent = build_agent()

    result = agent.invoke(
        {
            "messages": [
                SystemMessage(
                    content=SYSTEM_PROMPT
                ),
                HumanMessage(
                    content=question + "\n/no_think"
                ),
            ]
        },
        config={
            "recursion_limit": 6
        },
    )

    tool_results = [
        message
        for message in result["messages"]
        if isinstance(message, ToolMessage)
    ]

    # Nunca apresentar resposta comercial sem consulta.
    if not tool_results:
        print("\n=== CONSULTA NAO REALIZADA ===")

        print(
            "Nao foi possivel selecionar uma ferramenta "
            "autorizada para responder com seguranca. "
            "Nenhum resultado comercial foi apresentado."
        )

        return

    display_tool_results(tool_results)

    print(
        "\nObservacao: todos os dados comerciais sao sinteticos."
    )

    print("Agente executado com sucesso.")


if __name__ == "__main__":
    main()

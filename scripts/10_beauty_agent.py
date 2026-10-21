
"""Beauty Analytics AI Agent — LangGraph + Ollama + DuckDB."""

import json
import sys
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

from beauty_commerce.agent_policy import is_forecast_question
from beauty_commerce.analytics_tools import (
    sales_overview,
    top_brands,
    top_products,
)


# ==========================================================
# 1. FERRAMENTAS ANALITICAS AUTORIZADAS
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
Voce e o Beauty Analytics AI Agent, especializado
em analise comercial de uma empresa ficticia de beleza.

Escolha a ferramenta adequada para responder a pergunta.

Ferramentas:
- Faturamento geral: get_sales_overview.
- Ranking de marcas: get_top_brands.
- Ranking de produtos: get_top_products.

Regras:
- Responda apenas com base nos dados disponiveis.
- Para consultas comerciais, chame uma ferramenta.
- Nunca invente faturamento, marcas ou produtos.
- Nao execute SQL diretamente.
- Nao solicite credenciais ou arquivos externos.
- Os dados sao sinteticos.
- Nao produza previsoes.
- Se nenhuma ferramenta se aplicar, nao chame ferramentas.
"""


# ==========================================================
# 3. FORMATACAO MONETARIA
# ==========================================================

def format_brl(value):
    """Formata valores como moeda brasileira."""

    formatted = f"{value:,.2f}"

    return (
        "R$ "
        + formatted.replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )


# ==========================================================
# 4. CONSTRUCAO DO AGENTE LANGGRAPH
# ==========================================================

def build_agent():
    """Constroi o agente com ferramentas analiticas autorizadas."""

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
        response = model_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(MessagesState)

    graph.add_node("assistant", assistant_node)
    graph.add_node("tools", ToolNode(TOOLS))

    graph.add_edge(START, "assistant")

    graph.add_conditional_edges(
        "assistant",
        tools_condition,
    )

    # Finaliza apos a execucao das ferramentas.
    # Python formata os resultados sem usar texto do modelo.
    graph.add_edge("tools", END)

    return graph.compile()


# ==========================================================
# 5. APRESENTACAO DOS RESULTADOS
# ==========================================================

def display_tool_results(tool_results):
    """Apresenta resultados exclusivamente das ferramentas SQL."""

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
# 6. EXECUCAO PRINCIPAL
# ==========================================================

def main():

    question = (
        " ".join(sys.argv[1:]).strip()
        or "Qual foi o faturamento total e quantos meses foram analisados?"
    )

    print("\n=== BEAUTY ANALYTICS AI AGENT ===")
    print(f"Pergunta: {question}")

    # Aplica a politica antes de chamar o modelo.
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
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=question + "\n/no_think"),
            ]
        },
        config={"recursion_limit": 6},
    )

    tool_results = [
        message
        for message in result["messages"]
        if isinstance(message, ToolMessage)
    ]

    # Sem resultado de ferramenta, nao exibir dados comerciais.
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

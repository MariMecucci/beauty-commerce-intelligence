
"""Testa a integração Python com o Qwen3 executado no Ollama."""

from langchain_ollama import ChatOllama


def main():
    model = ChatOllama(
        model="qwen3:4b",
        base_url="http://127.0.0.1:11434",
        temperature=0,
        reasoning=False,
        num_ctx=4096,
        num_predict=200,
    )

    response = model.invoke([
        (
            "system",
            "Você é um assistente de análise de dados. "
            "Responda em português, de maneira objetiva. "
            "Ainda não possui acesso às tabelas comerciais."
        ),
        (
            "human",
            "Explique em uma frase como um agente de IA "
            "pode utilizar SQL para analisar vendas de cosméticos."
        ),
    ])

    print("\nRESPOSTA DO MODELO:")
    print(response.content)

    print("\nMODELO:")
    print(response.response_metadata.get("model", "qwen3:4b"))

    print("\nTeste de integração Python + Ollama concluído.")


if __name__ == "__main__":
    main()


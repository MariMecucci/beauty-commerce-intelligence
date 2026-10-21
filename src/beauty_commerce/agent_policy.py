
"""Regras deterministicas de escopo do Beauty Analytics AI Agent."""

import unicodedata


def normalize_text(text: str) -> str:
    """Padroniza texto e remove acentos."""

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
    """Identifica solicitacoes de previsao nao suportadas."""

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

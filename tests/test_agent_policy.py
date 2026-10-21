
"""Testes automatizados das regras de escopo do agente."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from beauty_commerce.agent_policy import (
    is_forecast_question,
    normalize_text,
)


class AgentPolicyTests(unittest.TestCase):

    def test_normalization(self):
        result = normalize_text("PREVISÃO DE FATURAMENTO")
        self.assertEqual(result, "previsao de faturamento")

    def test_forecast_question(self):
        self.assertTrue(
            is_forecast_question(
                "Qual será o faturamento no próximo ano?"
            )
        )

    def test_forecast_synonyms(self):
        questions = [
            "Faça uma previsão de vendas",
            "Quero uma projeção de faturamento",
            "Quanto a empresa vai faturar?",
            "Qual será o faturamento futuro?",
        ]

        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(
                    is_forecast_question(question)
                )

    def test_case_insensitive(self):
        self.assertTrue(
            is_forecast_question(
                "QUAL SERA O FATURAMENTO NO PROXIMO MES?"
            )
        )

    def test_historical_questions_allowed(self):
        questions = [
            "Qual foi o faturamento total?",
            "Quantos meses foram analisados?",
        ]

        for question in questions:
            with self.subTest(question=question):
                self.assertFalse(
                    is_forecast_question(question)
                )

    def test_product_and_brand_questions_allowed(self):
        questions = [
            "Quais são as três maiores marcas?",
            "Quais produtos tiveram maior faturamento?",
        ]

        for question in questions:
            with self.subTest(question=question):
                self.assertFalse(
                    is_forecast_question(question)
                )


if __name__ == "__main__":
    unittest.main()

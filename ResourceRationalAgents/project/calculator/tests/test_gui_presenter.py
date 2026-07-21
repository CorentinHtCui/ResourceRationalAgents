"""Desktop adapter tests that do not require a display server."""

import unittest

from calculator import Calculator
from calculator.adapters.gui import CalculatorPresenter


class CalculatorPresenterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.presenter = CalculatorPresenter(Calculator())

    def test_formats_successful_result_for_display(self) -> None:
        result = self.presenter.calculate("(2 + 3) * 4")

        self.assertEqual(result.text, "20")
        self.assertEqual(result.status, "Calculated")
        self.assertFalse(result.is_error)

    def test_preserves_expression_and_exposes_clear_error(self) -> None:
        expression = "4 / (2 - 2)"

        result = self.presenter.calculate(expression)

        self.assertEqual(result.text, expression)
        self.assertEqual(result.status, "Division by zero")
        self.assertTrue(result.is_error)

    def test_reports_invalid_expression_without_raising(self) -> None:
        result = self.presenter.calculate("2 +")

        self.assertEqual(result.text, "2 +")
        self.assertIn("unexpectedly", result.status)
        self.assertTrue(result.is_error)


if __name__ == "__main__":
    unittest.main()

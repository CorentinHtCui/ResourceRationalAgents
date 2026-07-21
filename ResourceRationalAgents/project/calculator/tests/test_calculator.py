"""Behavior tests through the calculator's public API."""

import unittest

from calculator import CalculationError, Calculator, DivisionByZeroError


class CalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = Calculator()

    def test_addition_and_subtraction(self) -> None:
        self.assertEqual(self.calculator.calculate("8 + 3 - 4"), 7.0)

    def test_multiplication_and_division(self) -> None:
        self.assertEqual(self.calculator.calculate("6 * 5 / 3"), 10.0)

    def test_operator_precedence(self) -> None:
        self.assertEqual(self.calculator.calculate("2 + 3 * 4"), 14.0)

    def test_parentheses_override_precedence(self) -> None:
        self.assertEqual(self.calculator.calculate("(2 + 3) * 4"), 20.0)

    def test_nested_parentheses_and_unary_signs(self) -> None:
        self.assertEqual(self.calculator.calculate("-(2 + (-3 * 4))"), 10.0)

    def test_decimal_and_scientific_number_literals(self) -> None:
        self.assertAlmostEqual(self.calculator.calculate(".5 + 1.5e1"), 15.5)

    def test_division_by_literal_zero_is_explicit(self) -> None:
        with self.assertRaisesRegex(DivisionByZeroError, "Division by zero"):
            self.calculator.calculate("4 / 0")

    def test_division_by_calculated_zero_is_explicit(self) -> None:
        with self.assertRaisesRegex(DivisionByZeroError, "Division by zero"):
            self.calculator.calculate("4 / (2 - 2)")

    def test_empty_expression_has_clear_error(self) -> None:
        with self.assertRaisesRegex(CalculationError, "Expression is empty"):
            self.calculator.calculate("   ")

    def test_invalid_character_reports_its_position(self) -> None:
        with self.assertRaisesRegex(CalculationError, "position 2"):
            self.calculator.calculate("2 & 3")

    def test_missing_parenthesis_has_clear_error(self) -> None:
        with self.assertRaisesRegex(CalculationError, "Expected '\\)'"):
            self.calculator.calculate("2 * (3 + 4")

    def test_implicit_multiplication_is_rejected(self) -> None:
        with self.assertRaisesRegex(CalculationError, "Unexpected token"):
            self.calculator.calculate("2(3 + 4)")

    def test_non_text_input_is_rejected_at_the_boundary(self) -> None:
        with self.assertRaisesRegex(CalculationError, "must be text"):
            self.calculator.calculate(2)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()

"""Public calculation use case."""

from calculator.domain.expression import evaluate_expression


class Calculator:
    """Evaluate arithmetic expressions independently of any user interface.

    ``calculate`` accepts expression text and returns a finite ``float``. Malformed
    input and division by zero use the public error types exported by ``calculator``.
    The class is stateless, so calls do not affect later calculations.
    """

    def calculate(self, expression: str) -> float:
        """Calculate one arithmetic expression."""

        return evaluate_expression(expression)

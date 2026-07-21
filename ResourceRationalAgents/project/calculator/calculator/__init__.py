"""Public API for the calculator application.

Use :class:`Calculator` to evaluate arithmetic expressions without involving the
command-line adapter.
"""

from calculator.application.calculate import Calculator
from calculator.domain.expression import CalculationError, DivisionByZeroError

__all__ = ["CalculationError", "Calculator", "DivisionByZeroError"]

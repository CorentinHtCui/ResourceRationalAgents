"""Deterministic arithmetic expression parsing and evaluation.

The parser implements the grammar directly and never delegates expression
evaluation to Python. Expected input failures are reported as ``CalculationError``;
division by zero is reported by its explicit ``DivisionByZeroError`` subtype.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re


class CalculationError(ValueError):
    """An expression cannot be calculated as supplied."""


class DivisionByZeroError(CalculationError):
    """An expression attempted division by zero."""


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    text: str
    position: int


_NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_SYMBOLS = {"+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "(": "LPAREN", ")": "RPAREN"}


def _tokenize(expression: str) -> tuple[_Token, ...]:
    tokens: list[_Token] = []
    position = 0
    while position < len(expression):
        character = expression[position]
        if character.isspace():
            position += 1
            continue
        if character in _SYMBOLS:
            tokens.append(_Token(_SYMBOLS[character], character, position))
            position += 1
            continue
        number = _NUMBER.match(expression, position)
        if number is not None:
            tokens.append(_Token("NUMBER", number.group(), position))
            position = number.end()
            continue
        raise CalculationError(f"Unexpected character {character!r} at position {position}")
    tokens.append(_Token("EOF", "", len(expression)))
    return tuple(tokens)


class _ExpressionParser:
    """Recursive-descent parser for the calculator's arithmetic grammar."""

    def __init__(self, expression: str) -> None:
        self._tokens = _tokenize(expression)
        self._index = 0

    @property
    def _current(self) -> _Token:
        return self._tokens[self._index]

    def parse(self) -> float:
        if self._current.kind == "EOF":
            raise CalculationError("Expression is empty")
        result = self._parse_expression()
        if self._current.kind != "EOF":
            raise CalculationError(
                f"Unexpected token {self._current.text!r} at position {self._current.position}"
            )
        if not math.isfinite(result):
            raise CalculationError("Result is not finite")
        return result

    def _advance(self) -> _Token:
        token = self._current
        self._index += 1
        return token

    def _accept(self, kind: str) -> bool:
        if self._current.kind != kind:
            return False
        self._advance()
        return True

    def _parse_expression(self) -> float:
        value = self._parse_term()
        while self._current.kind in {"PLUS", "MINUS"}:
            operator = self._advance().kind
            right = self._parse_term()
            value = value + right if operator == "PLUS" else value - right
        return value

    def _parse_term(self) -> float:
        value = self._parse_unary()
        while self._current.kind in {"STAR", "SLASH"}:
            operator = self._advance().kind
            right = self._parse_unary()
            if operator == "SLASH":
                if right == 0.0:
                    raise DivisionByZeroError("Division by zero")
                value /= right
            else:
                value *= right
        return value

    def _parse_unary(self) -> float:
        if self._accept("PLUS"):
            return self._parse_unary()
        if self._accept("MINUS"):
            return -self._parse_unary()
        return self._parse_primary()

    def _parse_primary(self) -> float:
        if self._current.kind == "NUMBER":
            return float(self._advance().text)
        if self._accept("LPAREN"):
            value = self._parse_expression()
            if not self._accept("RPAREN"):
                raise CalculationError(
                    f"Expected ')' at position {self._current.position}"
                )
            return value
        if self._current.kind == "EOF":
            raise CalculationError("Expression ended unexpectedly")
        raise CalculationError(
            f"Expected a number or '(' at position {self._current.position}"
        )


def evaluate_expression(expression: str) -> float:
    """Evaluate a basic arithmetic expression.

    Args:
        expression: Numbers, parentheses, and the ``+``, ``-``, ``*``, and ``/``
            operators. Standard precedence and unary signs are supported.

    Returns:
        The finite floating-point result.

    Raises:
        CalculationError: If the expression is empty, malformed, or non-finite.
        DivisionByZeroError: If any divisor evaluates to zero.
    """

    if not isinstance(expression, str):
        raise CalculationError("Expression must be text")
    return _ExpressionParser(expression).parse()

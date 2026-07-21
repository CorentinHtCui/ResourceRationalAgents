"""Command-line adapter for the calculator use case."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from typing import TextIO

from calculator import CalculationError, Calculator


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate basic arithmetic expressions.")
    parser.add_argument(
        "expression",
        nargs="?",
        help="expression to calculate; omit it to start interactive mode",
    )
    return parser


def _display(value: float) -> str:
    return format(value, ".15g")


def run_cli(
    calculator: Calculator,
    argv: Sequence[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output: TextIO = sys.stdout,
    error: TextIO = sys.stderr,
) -> int:
    """Translate command-line input and calculator outcomes to terminal I/O."""

    arguments = _parser().parse_args(argv)
    if arguments.expression is not None:
        try:
            print(_display(calculator.calculate(arguments.expression)), file=output)
        except CalculationError as exc:
            print(f"Error: {exc}", file=error)
            return 2
        return 0

    print("Basic calculator. Enter an expression, or 'quit' to exit.", file=output)
    while True:
        try:
            expression = input_fn("> ")
        except (EOFError, KeyboardInterrupt):
            print(file=output)
            return 0
        if expression.strip().lower() in {"quit", "exit"}:
            return 0
        try:
            print(_display(calculator.calculate(expression)), file=output)
        except CalculationError as exc:
            print(f"Error: {exc}", file=error)

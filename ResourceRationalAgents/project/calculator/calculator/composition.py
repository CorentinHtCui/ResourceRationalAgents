"""Composition root for the calculator command-line application."""

from collections.abc import Sequence

from calculator.adapters.cli import run_cli
from calculator.application.calculate import Calculator


def main(argv: Sequence[str] | None = None) -> int:
    """Construct the calculator and run its command-line adapter."""

    return run_cli(Calculator(), argv)


def gui_main() -> int:
    """Construct the calculator and run its desktop adapter."""

    from calculator.adapters.gui import run_gui

    return run_gui(Calculator())

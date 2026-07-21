# Basic calculator

This standard-library-only calculator supports addition, subtraction,
multiplication, division, unary signs, decimal numbers, and parentheses. It parses
the arithmetic grammar directly; it does not use `eval()`.

From this directory, calculate one expression:

```powershell
python -m calculator "(2 + 3) * 4"
```

Run `python -m calculator` without an expression for interactive mode. Enter
`quit` or `exit` to leave it. Invalid expressions are printed as explicit errors;
one-shot errors return exit status 2.

## Desktop interface

Launch the Tkinter desktop UI from this directory:

```powershell
python -m calculator.gui
```

The interface supports button and keyboard input. Press Enter to calculate, Escape
to clear, and Ctrl+A to select the current expression. Errors remain visible below
the display without discarding the expression.

Use the calculation logic without the CLI:

```python
from calculator import Calculator

result = Calculator().calculate("2 + 3 * 4")
```

Run the API tests with:

```powershell
python -m unittest discover -s tests -t . -v
```

## Architecture

- `calculator/domain/expression.py` owns deterministic parsing and arithmetic.
- `calculator/application/calculate.py` exposes the calculation use case.
- `calculator/adapters/cli.py` translates terminal input and output only.
- `calculator/adapters/gui.py` owns desktop presentation and Tkinter widgets.
- `calculator/composition.py` constructs the use case and CLI adapter.
- `calculator/__init__.py` is the stable public API used by tests and clients.

No outbound port is needed because basic calculation has no external capability.

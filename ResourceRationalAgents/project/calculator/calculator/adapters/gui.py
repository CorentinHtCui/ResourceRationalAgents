"""Tkinter desktop adapter for the calculator use case."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import font as tkfont

from calculator import CalculationError, Calculator


@dataclass(frozen=True, slots=True)
class DisplayResult:
    """Text and status produced by translating a calculation for the UI."""

    text: str
    status: str
    is_error: bool = False


class CalculatorPresenter:
    """Translate calculator outcomes without depending on Tkinter widgets."""

    def __init__(self, calculator: Calculator) -> None:
        self._calculator = calculator

    def calculate(self, expression: str) -> DisplayResult:
        """Return display-ready output for one expression."""

        try:
            value = self._calculator.calculate(expression)
        except CalculationError as exc:
            return DisplayResult(expression, str(exc), is_error=True)
        return DisplayResult(format(value, ".15g"), "Calculated")


class CalculatorWindow:
    """Responsive desktop calculator window."""

    _BACKGROUND = "#101318"
    _SURFACE = "#181D25"
    _NUMBER = "#242B36"
    _NUMBER_ACTIVE = "#303A48"
    _OPERATOR = "#263A45"
    _OPERATOR_ACTIVE = "#31505E"
    _ACCENT = "#55D6BE"
    _ACCENT_ACTIVE = "#75E3CE"
    _TEXT = "#F4F7FA"
    _MUTED = "#8E9AA9"
    _ERROR = "#FF7B8B"

    def __init__(self, root: tk.Tk, presenter: CalculatorPresenter) -> None:
        self._root = root
        self._presenter = presenter
        self._expression = tk.StringVar()
        self._status = tk.StringVar(value="Ready")
        self._build_window()
        self._build_display()
        self._build_keypad()
        self._bind_keyboard()

    def _build_window(self) -> None:
        self._root.title("Calculator")
        self._root.geometry("400x590")
        self._root.minsize(340, 520)
        self._root.configure(background=self._BACKGROUND)
        self._root.grid_columnconfigure(0, weight=1)
        self._root.grid_rowconfigure(1, weight=1)

    def _build_display(self) -> None:
        display = tk.Frame(self._root, background=self._BACKGROUND, padx=24, pady=20)
        display.grid(row=0, column=0, sticky="nsew")
        display.grid_columnconfigure(0, weight=1)

        title_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        tk.Label(
            display,
            text="CALCULATOR",
            anchor="w",
            background=self._BACKGROUND,
            foreground=self._ACCENT,
            font=title_font,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 14))

        self._entry = tk.Entry(
            display,
            textvariable=self._expression,
            justify="right",
            background=self._BACKGROUND,
            foreground=self._TEXT,
            insertbackground=self._ACCENT,
            selectbackground=self._OPERATOR,
            relief="flat",
            borderwidth=0,
            font=tkfont.Font(family="Segoe UI", size=30, weight="bold"),
        )
        self._entry.grid(row=1, column=0, sticky="ew", ipady=8)

        self._status_label = tk.Label(
            display,
            textvariable=self._status,
            anchor="e",
            background=self._BACKGROUND,
            foreground=self._MUTED,
            font=tkfont.Font(family="Segoe UI", size=10),
        )
        self._status_label.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self._entry.focus_set()

    def _build_keypad(self) -> None:
        keypad = tk.Frame(self._root, background=self._SURFACE, padx=14, pady=14)
        keypad.grid(row=1, column=0, sticky="nsew")
        for column in range(4):
            keypad.grid_columnconfigure(column, weight=1, uniform="key")
        for row in range(6):
            keypad.grid_rowconfigure(row, weight=1, uniform="key")

        keys = (
            (("(", "("), (")", ")"), ("⌫", self._backspace), ("C", self._clear)),
            (("7", "7"), ("8", "8"), ("9", "9"), ("÷", "/")),
            (("4", "4"), ("5", "5"), ("6", "6"), ("×", "*")),
            (("1", "1"), ("2", "2"), ("3", "3"), ("−", "-")),
            (("±", self._toggle_sign), ("0", "0"), (".", "."), ("+", "+")),
        )
        for row, key_row in enumerate(keys):
            for column, (label, action) in enumerate(key_row):
                is_operator = column == 3 or row == 0
                command = action if callable(action) else self._insert_command(action)
                self._button(keypad, label, command, is_operator).grid(
                    row=row,
                    column=column,
                    sticky="nsew",
                    padx=5,
                    pady=5,
                )

        self._button(keypad, "=", self._calculate, accent=True).grid(
            row=5,
            column=0,
            columnspan=4,
            sticky="nsew",
            padx=5,
            pady=5,
        )

    def _button(
        self,
        parent: tk.Widget,
        label: str,
        command: object,
        is_operator: bool = False,
        accent: bool = False,
    ) -> tk.Button:
        background = self._ACCENT if accent else self._OPERATOR if is_operator else self._NUMBER
        active = (
            self._ACCENT_ACTIVE
            if accent
            else self._OPERATOR_ACTIVE
            if is_operator
            else self._NUMBER_ACTIVE
        )
        foreground = self._BACKGROUND if accent else self._TEXT
        return tk.Button(
            parent,
            text=label,
            command=command,
            background=background,
            activebackground=active,
            foreground=foreground,
            activeforeground=foreground,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=tkfont.Font(family="Segoe UI", size=16, weight="bold"),
        )

    def _insert_command(self, text: str) -> object:
        return lambda: self._insert(text)

    def _insert(self, text: str) -> None:
        self._entry.insert(tk.INSERT, text)
        self._set_status("Ready")

    def _backspace(self) -> None:
        try:
            first = self._entry.index(tk.SEL_FIRST)
            last = self._entry.index(tk.SEL_LAST)
        except tk.TclError:
            cursor = self._entry.index(tk.INSERT)
            if cursor > 0:
                self._entry.delete(cursor - 1, cursor)
        else:
            self._entry.delete(first, last)
        self._set_status("Ready")

    def _clear(self) -> None:
        self._expression.set("")
        self._set_status("Cleared")

    def _toggle_sign(self) -> None:
        expression = self._expression.get().strip()
        if not expression:
            self._expression.set("-")
        elif expression.startswith("-(") and expression.endswith(")"):
            self._expression.set(expression[2:-1])
        else:
            self._expression.set(f"-({expression})")
        self._entry.icursor(tk.END)
        self._set_status("Ready")

    def _calculate(self, event: tk.Event[tk.Misc] | None = None) -> str | None:
        result = self._presenter.calculate(self._expression.get())
        if result.is_error:
            self._set_status(result.status, is_error=True)
            self._root.bell()
        else:
            self._expression.set(result.text)
            self._entry.icursor(tk.END)
            self._set_status(result.status)
        return "break" if event is not None else None

    def _set_status(self, message: str, *, is_error: bool = False) -> None:
        self._status.set(message)
        self._status_label.configure(foreground=self._ERROR if is_error else self._MUTED)

    def _bind_keyboard(self) -> None:
        self._root.bind("<Return>", self._calculate)
        self._root.bind("<KP_Enter>", self._calculate)
        self._root.bind("<Escape>", lambda _event: self._clear())
        self._root.bind("<Control-a>", self._select_all)

    def _select_all(self, _event: tk.Event[tk.Misc]) -> str:
        self._entry.selection_range(0, tk.END)
        self._entry.icursor(tk.END)
        return "break"


def run_gui(calculator: Calculator) -> int:
    """Create and run the calculator desktop interface."""

    root = tk.Tk()
    CalculatorWindow(root, CalculatorPresenter(calculator))
    root.mainloop()
    return 0

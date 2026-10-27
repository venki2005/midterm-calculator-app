import pytest
from unittest.mock import patch, MagicMock
from app.calculator_repl import calculator_repl
from app.exceptions import ValidationError, OperationError


def test_repl_help_and_exit(monkeypatch, capsys):
    inputs = iter(["help", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    calculator_repl()
    out = capsys.readouterr().out
    assert "Available commands:" in out
    assert "Goodbye!" in out


def test_repl_exit_save_failure(monkeypatch, capsys):
    inputs = iter(["exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    with patch("app.calculator.Calculator.save_history", side_effect=RuntimeError("Disk full")):
        calculator_repl()

    out = capsys.readouterr().out
    assert "Warning: Could not save history: Disk full" in out


def test_repl_history_empty_and_populated(monkeypatch, capsys):
    # Ensure history starts fresh by invoking 'clear' before checking empty history
    inputs = iter([
        "clear",
        "history",
        "add", "5", "3",
        "history",
        "exit"
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    calculator_repl()
    out = capsys.readouterr().out
    assert "No calculations in history" in out
    assert "Calculation History:" in out


def test_repl_clear(monkeypatch, capsys):
    inputs = iter(["clear", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    calculator_repl()
    out = capsys.readouterr().out
    assert "History cleared" in out


def test_repl_undo_and_redo(monkeypatch, capsys):
    inputs = iter([
        "undo",        # nothing to undo
        "redo",        # nothing to redo
        "add", "2", "2",
        "undo",        # success
        "redo",        # success
        "exit"
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    calculator_repl()
    out = capsys.readouterr().out
    assert "Nothing to undo" in out
    assert "Nothing to redo" in out
    assert "Operation undone" in out
    assert "Operation redone" in out


def test_repl_save_and_load_success_and_failure(monkeypatch, capsys):
    # Success paths
    inputs = iter(["save", "load", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with patch("app.calculator.Calculator.save_history"), \
         patch("app.calculator.Calculator.load_history"):
        calculator_repl()
    out = capsys.readouterr().out
    assert "History saved successfully" in out
    assert "History loaded successfully" in out

    # Failure paths
    fail_inputs = iter(["save", "load", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(fail_inputs))
    with patch("app.calculator.Calculator.save_history", side_effect=Exception("Disk fail")), \
         patch("app.calculator.Calculator.load_history", side_effect=Exception("File fail")):
        calculator_repl()
    fail_out = capsys.readouterr().out
    assert "Error saving history: Disk fail" in fail_out
    assert "Error loading history: File fail" in fail_out


def test_repl_operation_cancel(monkeypatch, capsys):
    inputs = iter([
        "add", "cancel",
        "add", "5", "cancel",
        "exit"
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    calculator_repl()
    out = capsys.readouterr().out
    assert out.count("Operation cancelled") >= 2


def test_repl_operation_errors(monkeypatch, capsys):
    inputs = iter([
        "divide", "5", "0",
        "add", "1", "1",
        "exit"
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    mock_perform = MagicMock()
    mock_perform.side_effect = [
        ValidationError("Division error"),
        Exception("Unexpected arithmetic error")
    ]

    with patch("app.calculator.Calculator.perform_operation", mock_perform):
        calculator_repl()

    out = capsys.readouterr().out
    assert "Error: Division error" in out
    assert "Unexpected error: Unexpected arithmetic error" in out


def test_repl_unknown_command(monkeypatch, capsys):
    inputs = iter(["unknown_cmd", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    calculator_repl()
    out = capsys.readouterr().out
    assert "Unknown command: 'unknown_cmd'" in out


def test_repl_interrupt_and_eof(monkeypatch, capsys):
    inputs = iter([KeyboardInterrupt, EOFError])

    def mock_input(_):
        val = next(inputs)
        if isinstance(val, type) and issubclass(val, BaseException):
            raise val
        return val

    monkeypatch.setattr("builtins.input", mock_input)

    calculator_repl()
    out = capsys.readouterr().out
    assert "Operation cancelled" in out
    assert "Input terminated. Exiting..." in out


def test_repl_inner_exception(monkeypatch, capsys):
    inputs = iter([RuntimeError("Loop error"), "exit"])

    def mock_input(_):
        val = next(inputs)
        if isinstance(val, Exception):
            raise val
        return val

    monkeypatch.setattr("builtins.input", mock_input)
    calculator_repl()
    out = capsys.readouterr().out
    assert "Error: Loop error" in out


def test_repl_fatal_error():
    with patch("app.calculator_repl.Calculator", side_effect=RuntimeError("Init crash")):
        with pytest.raises(RuntimeError, match="Init crash"):
            calculator_repl()
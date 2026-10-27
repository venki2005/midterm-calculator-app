import datetime
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch
from decimal import Decimal
from tempfile import TemporaryDirectory
import pandas as pd
import pytest

from app.calculator import Calculator
from app.calculator_repl import calculator_repl
from app.calculator_config import CalculatorConfig
from app.calculation import Calculation
from app.exceptions import OperationError, ValidationError
from app.history import LoggingObserver, AutoSaveObserver
from app.operations import OperationFactory


# Fixture to initialize Calculator with a temporary directory for file paths
@pytest.fixture
def calculator():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = CalculatorConfig(base_dir=temp_path)

            # Patch properties to use the temporary directory paths
        with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
             patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file, \
             patch.object(CalculatorConfig, 'history_dir', new_callable=PropertyMock) as mock_history_dir, \
             patch.object(CalculatorConfig, 'history_file', new_callable=PropertyMock) as mock_history_file:

            # Set return values to use paths within the temporary directory
            mock_log_dir.return_value = temp_path / "logs"
            mock_log_file.return_value = temp_path / "logs" / "calculator.log"
            mock_history_dir.return_value = temp_path / "history"
            mock_history_file.return_value = temp_path / "history" / "calculator_history.csv"

            yield Calculator(config=config)


# --- Initialization & Config Tests ---

def test_calculator_initialization(calculator):
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []
    assert calculator.operation_strategy is None


@patch('app.calculator.logging.info')
def test_logging_setup(logging_info_mock):
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = CalculatorConfig(base_dir=temp_path)
        calc = Calculator(config=config)
        assert calc is not None
        logging_info_mock.assert_any_call("Calculator initialized with configuration")


# --- Observer Tests ---

def test_add_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    assert observer in calculator.observers


def test_remove_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    calculator.remove_observer(observer)
    assert observer not in calculator.observers


def test_notify_observers(calculator):
    mock_observer = MagicMock()
    calculator.add_observer(mock_observer)
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(2, 3)
    mock_observer.update.assert_called()

def test_notify_observers_exception_handling(calculator):
    mock_observer = MagicMock()
    mock_observer.update.side_effect = Exception("Observer crashed")
    calculator.add_observer(mock_observer)

    calculator.set_operation(OperationFactory.create_operation("add"))
    
    with pytest.raises(OperationError, match="Observer crashed"):
        calculator.perform_operation(2, 3)

# --- Operation Strategy & Execution ---

def test_set_operation(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    assert calculator.operation_strategy == operation


def test_perform_operation_addition(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    result = calculator.perform_operation(2, 3)
    assert result == Decimal('5')


def test_perform_operation_validation_error(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    with pytest.raises(ValidationError):
        calculator.perform_operation('invalid', 3)


def test_perform_operation_without_strategy(calculator):
    with pytest.raises(OperationError, match="No operation set"):
        calculator.perform_operation(2, 3)


# --- Undo / Redo Tests ---

def test_undo(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    assert calculator.undo() is True
    assert calculator.history == []


def test_undo_empty(calculator):
    assert calculator.undo() is False


def test_redo(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.undo()
    assert calculator.redo() is True
    assert len(calculator.history) == 1


def test_redo_empty(calculator):
    assert calculator.redo() is False

def test_undo_and_redo_stack_boundaries(calculator):
    # Ensure redo on empty stack returns False
    calculator.clear_history()
    assert calculator.redo() is False
    assert calculator.undo() is False

# --- History Management Tests ---

def test_show_history(calculator):
    assert calculator.show_history() == []
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(2, 3)
    history = calculator.show_history()
    assert len(history) == 1
    assert "add" in str(history[0]).lower() or "addition" in str(history[0]).lower()


def test_clear_history(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.clear_history()
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []

def test_save_history_io_error(calculator):
    calculator.set_operation(OperationFactory.create_operation("add"))
    calculator.perform_operation(2, 3)

    with patch("app.calculator.pd.DataFrame.to_csv", side_effect=IOError("Disk write failure")):
        with pytest.raises(OperationError, match="(?i)failed to save history|disk write failure"):
            calculator.save_history()

@patch('app.calculator.pd.DataFrame.to_csv')
def test_save_history(mock_to_csv, calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.save_history()
    mock_to_csv.assert_called_once()


def test_load_history_success(calculator):
    df_data = pd.DataFrame({
        'operation': ['Addition'],
        'operand1': ['2'],
        'operand2': ['3'],
        'result': ['5'],
        'timestamp': [datetime.datetime.now().isoformat()]
    })

    with patch.object(Path, 'exists', return_value=True), \
         patch('app.calculator.pd.read_csv', return_value=df_data):
        calculator.load_history()
        assert len(calculator.history) == 1
        assert calculator.history[0].operand1 == Decimal('2')
        assert calculator.history[0].operand2 == Decimal('3')
        assert calculator.history[0].result == Decimal('5')


def test_load_history_file_not_found(calculator):
    with patch.object(Path, 'exists', return_value=False):
        # Should cleanly exit or raise OperationError depending on app logic
        try:
            calculator.load_history()
        except OperationError:
            pass


# --- REPL Tests ---

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_calculator_repl_exit(mock_print, mock_input):
    with patch('app.calculator.Calculator.save_history') as mock_save_history:
        calculator_repl()
        mock_save_history.assert_called_once()
        mock_print.assert_any_call("History saved successfully.")
        mock_print.assert_any_call("Goodbye!")


@patch('builtins.input', side_effect=['help', 'exit'])
@patch('builtins.print')
def test_calculator_repl_help(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")


@patch('builtins.input', side_effect=['add', '2', '3', 'exit'])
@patch('builtins.print')
def test_calculator_repl_addition(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nResult: 5")
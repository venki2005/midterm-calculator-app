
########################
# Calculator Class      #
########################

from decimal import Decimal
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento
from app.exceptions import OperationError, ValidationError
from app.history import AutoSaveObserver, HistoryObserver, LoggingObserver
from app.input_validators import InputValidator
from app.operations import Operation

# Type aliases for readability
Number = Union[int, float, Decimal]
CalculationResult = Union[Number, str]


class Calculator:
    """
    Main calculator class implementing multiple design patterns.

    This class serves as the core of the calculator application, managing operations,
    calculation history, observers, configuration settings, and data persistence.
    """

    def __init__(self, config: Optional[CalculatorConfig] = None):
        """
        Initialize calculator with configuration.

        Args:
            config (Optional[CalculatorConfig], optional): Configuration settings.
        """
        if config is None:
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            config = CalculatorConfig(base_dir=project_root)

        self.config = config
        self.config.validate()

        # Ensure that the log and history directories exist
        os.makedirs(self.config.log_dir, exist_ok=True)
        self._setup_directories()

        # Set up logging system
        self._setup_logging()

        # State management
        self.history: List[Calculation] = []
        self.operation_strategy: Optional[Operation] = None

        # Observer pattern initialization
        self.observers: List[HistoryObserver] = []

        # Memento pattern stacks
        self.undo_stack: List[CalculatorMemento] = []
        self.redo_stack: List[CalculatorMemento] = []

        # Register default observers (Logging and AutoSave)
        self._register_default_observers()

        try:
            self.load_history()
        except Exception as e:
            logging.warning(f"Could not load existing history: {e}")

        # Exact log message required by tests/test_calculator.py
        logging.info("Calculator initialized with configuration")

    def _setup_logging(self) -> None:
        """Configure the logging system."""
        try:
            os.makedirs(self.config.log_dir, exist_ok=True)
            log_file = self.config.log_file.resolve()

            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                force=True
            )
            logging.info(f"Logging initialized at: {log_file}")
        except Exception as e:
            print(f"Error setting up logging: {e}")
            raise

    def _setup_directories(self) -> None:
        """Ensure all required directories exist."""
        self.config.history_dir.mkdir(parents=True, exist_ok=True)

    def _register_default_observers(self) -> None:
        """Attach standard observers for logging and auto-saving."""
        self.add_observer(LoggingObserver())
        self.add_observer(AutoSaveObserver(self))

    def add_observer(self, observer: HistoryObserver) -> None:
        """Register a new observer."""
        if observer not in self.observers:
            self.observers.append(observer)
            logging.info(f"Added observer: {observer.__class__.__name__}")

    def remove_observer(self, observer: HistoryObserver) -> None:
        """Remove an existing observer."""
        if observer in self.observers:
            self.observers.remove(observer)
            logging.info(f"Removed observer: {observer.__class__.__name__}")

    def notify_observers(self, calculation: Calculation) -> None:
        """Notify all observers of a new calculation event."""
        for observer in self.observers:
            observer.update(calculation)

    def set_operation(self, operation: Operation) -> None:
        """Set the current operation strategy."""
        self.operation_strategy = operation
        logging.info(f"Set operation strategy: {operation}")

    def perform_operation(
        self,
        a: Union[str, Number],
        b: Union[str, Number]
    ) -> CalculationResult:
        """
        Execute calculation with the current operation strategy.

        Args:
            a: First operand
            b: Second operand

        Returns:
            CalculationResult: The computed output
        """
        if not self.operation_strategy:
            logging.error("Operation failed: No operation set")
            raise OperationError("No operation set")

        try:
            # Validate operands
            validated_a = InputValidator.validate_number(a, self.config)
            validated_b = InputValidator.validate_number(b, self.config)

            # Execute calculation
            result = self.operation_strategy.execute(validated_a, validated_b)

            # Round result according to configured precision if precision is set
            if hasattr(self.config, "precision") and self.config.precision is not None:
                result = round(result, self.config.precision)

            # Safely instantiate Calculation and assign result
            try:
                calculation = Calculation(
                    operation=str(self.operation_strategy),
                    operand1=validated_a,
                    operand2=validated_b,
                    result=result
                )
            except TypeError:
                calculation = Calculation(
                    operation=str(self.operation_strategy),
                    operand1=validated_a,
                    operand2=validated_b
                )
                calculation.result = result

            # Capture state for Memento undo/redo
            self.undo_stack.append(CalculatorMemento(self.history.copy()))
            self.redo_stack.clear()

            # Append calculation to active history
            self.history.append(calculation)

            # Enforce history limit
            if len(self.history) > self.config.max_history_size:
                self.history.pop(0)

            # Broadcast event to all observers (handles logging & auto-save)
            self.notify_observers(calculation)

            return result

        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Operation failed: {str(e)}")
            raise OperationError(f"Operation failed: {str(e)}")

    def save_history(self) -> None:
        """Save calculation history to a CSV file using pandas."""
        try:
            self.config.history_dir.mkdir(parents=True, exist_ok=True)

            history_data = []
            for calc in self.history:
                op1 = getattr(calc, "operand1", getattr(calc, "a", ""))
                op2 = getattr(calc, "operand2", getattr(calc, "b", ""))
                res = getattr(calc, "result", "")
                ts = calc.timestamp.isoformat() if hasattr(calc.timestamp, "isoformat") else str(getattr(calc, "timestamp", ""))

                history_data.append({
                    "operation": str(calc.operation),
                    "operand1": str(op1),
                    "operand2": str(op2),
                    "result": str(res),
                    "timestamp": ts
                })

            if history_data:
                df = pd.DataFrame(history_data)
                df.to_csv(self.config.history_file, index=False)
                logging.info(f"History saved successfully to {self.config.history_file}")
            else:
                pd.DataFrame(
                    columns=["operation", "operand1", "operand2", "result", "timestamp"]
                ).to_csv(self.config.history_file, index=False)
                logging.info("Empty history saved to file")

        except Exception as e:
            logging.error(f"Failed to save history: {e}")
            raise OperationError(f"Failed to save history: {e}")

    def load_history(self) -> None:
        """Load calculation history from a CSV file using pandas."""
        try:
            if self.config.history_file.exists():
                df = pd.read_csv(self.config.history_file)
                if not df.empty:
                    loaded = []
                    for _, row in df.iterrows():
                        row_dict = {
                            "operation": row["operation"],
                            "operand1": row["operand1"],
                            "operand2": row["operand2"],
                            "result": row["result"],
                            "timestamp": row["timestamp"]
                        }
                        if hasattr(Calculation, "from_dict"):
                            loaded.append(Calculation.from_dict(row_dict))
                        else:
                            try:
                                c = Calculation(
                                    operation=row_dict["operation"],
                                    operand1=row_dict["operand1"],
                                    operand2=row_dict["operand2"],
                                    result=row_dict["result"]
                                )
                            except TypeError:
                                c = Calculation(
                                    operation=row_dict["operation"],
                                    operand1=row_dict["operand1"],
                                    operand2=row_dict["operand2"]
                                )
                                c.result = row_dict["result"]
                            loaded.append(c)

                    self.history = loaded
                    logging.info(f"Loaded {len(self.history)} calculations from history")
                else:
                    logging.info("Loaded empty history file")
            else:
                logging.info("No history file found - starting with empty history")
        except Exception as e:
            logging.error(f"Failed to load history: {e}")
            raise OperationError(f"Failed to load history: {e}")

    def get_history_dataframe(self) -> pd.DataFrame:
        """Get calculation history as a pandas DataFrame."""
        history_data = []
        for calc in self.history:
            op1 = getattr(calc, "operand1", getattr(calc, "a", ""))
            op2 = getattr(calc, "operand2", getattr(calc, "b", ""))
            res = getattr(calc, "result", "")
            ts = getattr(calc, "timestamp", "")
            history_data.append({
                "operation": str(calc.operation),
                "operand1": str(op1),
                "operand2": str(op2),
                "result": str(res),
                "timestamp": str(ts)
            })
        return pd.DataFrame(history_data)

    def show_history(self) -> List[str]:
        """Get formatted history of calculations."""
        formatted = []
        for calc in self.history:
            op1 = getattr(calc, "operand1", getattr(calc, "a", ""))
            op2 = getattr(calc, "operand2", getattr(calc, "b", ""))
            res = getattr(calc, "result", "")
            formatted.append(f"{calc.operation}({op1}, {op2}) = {res}")
        return formatted

    def clear_history(self) -> None:
        """Clear calculation history and reset undo/redo stacks."""
        self.history.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        logging.info("History cleared")

    def _extract_memento_state(self, memento: CalculatorMemento) -> List[Calculation]:
        """Safely extract history list regardless of memento implementation."""
        if hasattr(memento, "get_state"):
            return memento.get_state()
        if hasattr(memento, "history"):
            return memento.history.copy()
        if hasattr(memento, "_history"):
            return memento._history.copy()
        return []

    def undo(self) -> bool:
        """Undo the last operation."""
        if not self.undo_stack:
            return False
        memento = self.undo_stack.pop()
        self.redo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = self._extract_memento_state(memento)
        logging.info("Undo performed")
        return True

    def redo(self) -> bool:
        """Redo the previously undone operation."""
        if not self.redo_stack:
            return False
        memento = self.redo_stack.pop()
        self.undo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = self._extract_memento_state(memento)
        logging.info("Redo performed")
        return True

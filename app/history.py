"""
History Management and Observer Pattern Implementations.

This module provides state restoration (undo/redo via Memento pattern),
pandas CSV persistence, and observer implementations for automated logging
and persistence.
"""

from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import Config
from app.calculator_memento import CalculatorMemento
from app.exceptions import OperationError
from app.logger import logger


class HistoryManager:
    """Manages calculation history, state restoration, and CSV persistence."""

    def __init__(self) -> None:
        self._history: List[Calculation] = []
        self._undo_stack: List[CalculatorMemento] = []
        self._redo_stack: List[CalculatorMemento] = []

    @property
    def history(self) -> List[Calculation]:
        """Return a copy of the current calculation history list."""
        return list(self._history)

    def add_calculation(self, calculation: Calculation) -> None:
        """Add a calculation to history and record a state snapshot."""
        self._save_memento()
        self._redo_stack.clear()
        self._history.append(calculation)

        # Enforce maximum history capacity
        if len(self._history) > Config.MAX_HISTORY_SIZE:
            self._history.pop(0)

    def _save_memento(self) -> None:
        """Store a snapshot of the current history in the undo stack."""
        self._undo_stack.append(CalculatorMemento(self._history))

    def undo(self) -> Optional[Calculation]:
        """Undo the last calculation and return the previous head calculation."""
        if not self._undo_stack:
            return None
        self._redo_stack.append(CalculatorMemento(self._history))
        memento = self._undo_stack.pop()
        self._history = memento.get_state()
        return self._history[-1] if self._history else None

    def redo(self) -> Optional[Calculation]:
        """Redo the most recently reverted calculation."""
        if not self._redo_stack:
            return None
        self._undo_stack.append(CalculatorMemento(self._history))
        memento = self._redo_stack.pop()
        self._history = memento.get_state()
        return self._history[-1] if self._history else None

    def clear(self) -> None:
        """Clear calculation history and record undo point."""
        self._save_memento()
        self._redo_stack.clear()
        self._history.clear()

    def save_to_csv(self, file_path: Optional[Path | str] = None) -> None:
        """Serialize current calculation history to a CSV file."""
        path = Path(file_path or Config.HISTORY_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            records = [c.to_dict() for c in self._history]
            df = pd.DataFrame(records)
            df.to_csv(path, index=False, encoding=Config.DEFAULT_ENCODING)
            logger.info("HISTORY PERSISTENCE: Successfully saved %d calculations to '%s'", len(self._history), path)
        except Exception as exc:
            logger.error("HISTORY PERSISTENCE ERROR: Failed writing CSV to '%s': %s", path, exc)
            raise OperationError(f"Could not save history to file: {exc}") from exc

    def load_from_csv(self, file_path: Optional[Path | str] = None) -> int:
        """Deserialize calculations from a CSV file into history."""
        path = Path(file_path or Config.HISTORY_FILE)
        if not path.exists():
            logger.error("HISTORY LOAD ERROR: File '%s' does not exist.", path)
            raise OperationError(f"History file '{path}' does not exist.")
        try:
            df = pd.read_csv(path, encoding=Config.DEFAULT_ENCODING)
            required_cols = {"operation", "operand_a", "operand_b", "result", "timestamp"}
            if not required_cols.issubset(df.columns):
                logger.error("HISTORY LOAD ERROR: CSV file is missing required columns.")
                raise OperationError("Malformed CSV: missing required columns.")

            self._save_memento()
            self._redo_stack.clear()
            self._history = [Calculation.from_dict(row.to_dict()) for _, row in df.iterrows()]
            logger.info("HISTORY LOAD: Successfully loaded %d calculations from '%s'", len(self._history), path)
            return len(self._history)
        except OperationError:
            raise
        except Exception as exc:
            logger.error("HISTORY LOAD ERROR: Failed reading CSV '%s': %s", path, exc)
            raise OperationError(f"Malformed CSV file: {exc}") from exc


class HistoryObserver(ABC):
    """Abstract base class for calculation observers."""

    @abstractmethod
    def update(self, calculation: Calculation) -> None:
        """Handle new calculation event."""
        pass  # pragma: no cover


class LoggingObserver(HistoryObserver):
    """Observer that writes calculation details to application logs."""

    def update(self, calculation: Calculation) -> None:
        """Log calculation details using consistent attribute names."""
        if calculation is None:
            raise AttributeError("Calculation cannot be None")

        # Resolves attribute dynamically regardless of naming convention used
        op_a = getattr(calculation, "a", getattr(calculation, "operand1", None))
        op_b = getattr(calculation, "b", getattr(calculation, "operand2", None))

        logger.info(
            "CALCULATION PERFORMED: %s(operand_a=%s, operand_b=%s) = %s [timestamp=%s]",
            calculation.operation,
            op_a,
            op_b,
            calculation.result,
            getattr(calculation, "timestamp", "N/A"),
        )


class AutoSaveObserver(HistoryObserver):
    """Observer that automatically triggers CSV persistence on new calculations."""

    def __init__(self, target: Any) -> None:
        """
        Initialize the AutoSaveObserver.
        
        Accepts either a Calculator facade (with 'save_history' and 'config')
        or a HistoryManager instance directly.
        """
        self.target = target

    def update(self, calculation: Calculation) -> None:
        """Trigger auto-save if enabled in configuration."""
        if calculation is None:
            raise AttributeError("Calculation cannot be None")

        should_save = False
        if hasattr(self.target, "config") and hasattr(self.target.config, "auto_save"):
            should_save = bool(self.target.config.auto_save)
        else:
            should_save = getattr(Config, "AUTO_SAVE", True)

        if should_save:
            try:
                if hasattr(self.target, "save_history"):
                    self.target.save_history()
                elif hasattr(self.target, "save_to_csv"):
                    self.target.save_to_csv()
                logger.info("HISTORY AUTO-SAVE: Calculation history successfully auto-saved.")
            except Exception as exc:
                logger.error("HISTORY AUTO-SAVE ERROR: Failed to auto-save history: %s", exc)
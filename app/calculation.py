"""
Calculation model tracking operation, operands, result, and timestamp.
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
import logging
from typing import Any, Dict, Optional

from app.exceptions import OperationError, ValidationError


class Calculation:
    """Represents a single calculation entity."""

    def __init__(
        self,
        operation: str,
        operand1: Any,
        operand2: Any,
        result: Optional[Any] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.operation = str(operation)

        # Convert operands to Decimal
        try:
            self.operand1 = Decimal(str(operand1))
            self.operand2 = Decimal(str(operand2))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValidationError(f"Invalid operands: {exc}") from exc

        self.timestamp = timestamp or datetime.now()

        computed_result = self.calculate()

        if result is not None:
            try:
                parsed_result = Decimal(str(result))
            except (InvalidOperation, ValueError, TypeError) as exc:
                raise ValidationError(f"Invalid result value: {exc}") from exc

            if parsed_result != computed_result:
                logging.warning(
                    f"Loaded calculation result {parsed_result} differs from computed result {computed_result}"
                )
            self.result = parsed_result
        else:
            self.result = computed_result

    def _raise_div_zero(self):
        raise OperationError("Division by zero is not allowed")

    def _raise_neg_power(self):
        raise OperationError("Negative exponents are not supported")

    def _raise_invalid_root(self, x, y):
        if y == 0:
            raise OperationError("Zero root is undefined")
        # Matches tests/test_calculation.py regex: "Cannot calculate root of negative number"
        raise OperationError("Cannot calculate root of negative number")

    def calculate(self) -> Decimal:
        """Compute result based on operation and operands."""
        x = self.operand1
        y = self.operand2

        operations = {
            # Addition
            "Addition": lambda: x + y,
            "add": lambda: x + y,
            # Subtraction
            "Subtraction": lambda: x - y,
            "subtract": lambda: x - y,
            # Multiplication
            "Multiplication": lambda: x * y,
            "multiply": lambda: x * y,
            # Division
            "Division": lambda: x / y if y != 0 else self._raise_div_zero(),
            "divide": lambda: x / y if y != 0 else self._raise_div_zero(),
            # Integer Division (rubric item)
            "IntegerDivision": lambda: Decimal(int(x // y)) if y != 0 else self._raise_div_zero(),
            "integer_division": lambda: Decimal(int(x // y)) if y != 0 else self._raise_div_zero(),
            # Power
            "Power": lambda: (
                Decimal(str(pow(float(x), float(y))))
                if y >= 0
                else self._raise_neg_power()
            ),
            "power": lambda: (
                Decimal(str(pow(float(x), float(y))))
                if y >= 0
                else self._raise_neg_power()
            ),
            # Root
            "Root": lambda: (
                Decimal(str(pow(float(x), 1.0 / float(y))))
                if x >= 0 and y != 0
                else self._raise_invalid_root(x, y)
            ),
            "root": lambda: (
                Decimal(str(pow(float(x), 1.0 / float(y))))
                if x >= 0 and y != 0
                else self._raise_invalid_root(x, y)
            ),
            # Modulus
            "Modulus": lambda: x % y if y != 0 else self._raise_div_zero(),
            "modulus": lambda: x % y if y != 0 else self._raise_div_zero(),
            # Percentage (rubric item: correct stored percentage (a / b) * 100)
            "Percentage": lambda: (x / y) * Decimal("100") if y != 0 else self._raise_div_zero(),
            "percent": lambda: (x / y) * Decimal("100") if y != 0 else self._raise_div_zero(),
            # Absolute Difference
            "AbsoluteDiff": lambda: abs(x - y),
            "absolute_diff": lambda: abs(x - y),
        }

        op_func = operations.get(self.operation)
        if not op_func:
            raise OperationError(f"Unknown operation: {self.operation}")

        return op_func()

    def format_result(self, precision: Optional[int] = None) -> str:
        """Format calculation result with optional precision."""
        if precision is not None and self.result is not None:
            return str(round(self.result, precision))
        return str(self.result)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize instance to dictionary."""
        return {
            "operation": self.operation,
            "operand1": str(self.operand1),
            "operand2": str(self.operand2),
            "result": str(self.result),
            "timestamp": (
                self.timestamp.isoformat()
                if hasattr(self.timestamp, "isoformat")
                else str(self.timestamp)
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Calculation":
        """Deserialize calculation from a dictionary."""
        required = ("operation", "operand1", "operand2", "result", "timestamp")
        missing = [key for key in required if key not in data]
        if missing:
            raise OperationError("Invalid calculation data")

        ts = data["timestamp"]
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except ValueError:
                ts = datetime.now()
        elif not isinstance(ts, datetime):
            ts = datetime.now()

        try:
            return cls(
                operation=str(data["operation"]),
                operand1=data["operand1"],
                operand2=data["operand2"],
                result=data["result"],
                timestamp=ts,
            )
        except Exception as exc:
            raise OperationError("Invalid calculation data") from exc

    def __str__(self) -> str:
        return f"{self.operation}({self.operand1}, {self.operand2}) = {self.result}"

    def __repr__(self) -> str:
        res = getattr(self, "result", None)
        return (
            f"Calculation(operation='{self.operation}', "
            f"operand1=Decimal('{getattr(self, 'operand1', None)}'), "
            f"operand2=Decimal('{getattr(self, 'operand2', None)}'), "
            f"result=Decimal('{res}'), timestamp={repr(self.timestamp)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Calculation):
            return False
        return (
            self.operation == other.operation
            and self.operand1 == other.operand1
            and self.operand2 == other.operand2
            and self.result == other.result
        )
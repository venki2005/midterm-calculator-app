"""
Operation classes implementing the Command/Strategy pattern for the calculator,
and OperationFactory for dynamic operation creation.
"""

from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Type

from app.exceptions import OperationError


class Operation(ABC):
    """Abstract base class for all calculator operations."""

    @abstractmethod
    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        Execute the operation on two Decimal operands.

        Args:
            a: First operand
            b: Second operand

        Returns:
            Decimal: Computed result
        """
        pass  # pragma: no cover

    def __str__(self) -> str:
        """Return the lowercase command name of the operation."""
        return self.__class__.__name__.lower()


class Add(Operation):
    """Addition operation: a + b."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        return a + b

    def __str__(self) -> str:
        return "add"


class Subtract(Operation):
    """Subtraction operation: a - b."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        return a - b

    def __str__(self) -> str:
        return "subtract"


class Multiply(Operation):
    """Multiplication operation: a * b."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        return a * b

    def __str__(self) -> str:
        return "multiply"


class Divide(Operation):
    """Division operation: a / b."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        if b == Decimal("0"):
            raise OperationError("Cannot divide by zero")
        try:
            return a / b
        except InvalidOperation as exc:
            raise OperationError(f"Division failed: {exc}") from exc

    def __str__(self) -> str:
        return "divide"


class IntegerDivision(Operation):
    """Integer (floor) division operation: a // b."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        if b == Decimal("0"):
            raise OperationError("Cannot divide by zero")
        try:
            return Decimal(int(a // b))
        except (InvalidOperation, ValueError) as exc:
            raise OperationError(f"Integer division failed: {exc}") from exc

    def __str__(self) -> str:
        return "integer_division"


class Percent(Operation):
    """
    Percentage operation: calculates what percentage 'a' is of 'b' ((a / b) * 100).
    """

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        if b == Decimal("0"):
            raise OperationError("Cannot calculate percentage with zero base")
        try:
            return (a / b) * Decimal("100")
        except InvalidOperation as exc:
            raise OperationError(f"Percent calculation failed: {exc}") from exc

    def __str__(self) -> str:
        return "percent"


class Power(Operation):
    """Exponentiation operation: a ** b."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        try:
            if b == Decimal("0"):
                return Decimal("1")
            if b == b.to_integral_value():
                return a ** int(b)
            return Decimal(str(pow(float(a), float(b))))
        except Exception as exc:
            raise OperationError(f"Power calculation failed: {exc}") from exc

    def __str__(self) -> str:
        return "power"


class Root(Operation):
    """Nth root operation: b-th root of a (a ** (1 / b))."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        if b == Decimal("0"):
            raise OperationError("Cannot compute zeroth root")
        if a < Decimal("0"):
            raise OperationError("Cannot calculate root of negative number")
        try:
            root_val = pow(float(a), 1.0 / float(b))
            return Decimal(str(root_val))
        except Exception as exc:
            raise OperationError(f"Root calculation failed: {exc}") from exc

    def __str__(self) -> str:
        return "root"


class Modulus(Operation):
    """Modulus (remainder) operation: a % b."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        if b == Decimal("0"):
            raise OperationError("Cannot perform modulus by zero")
        try:
            return a % b
        except InvalidOperation as exc:
            raise OperationError(f"Modulus operation failed: {exc}") from exc

    def __str__(self) -> str:
        return "modulus"


class AbsoluteDiff(Operation):
    """Absolute difference operation: |a - b|."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        return abs(a - b)

    def __str__(self) -> str:
        return "absolute_diff"


class OperationFactory:
    """Factory for registering, listing, and instantiating operations."""

    _operations: Dict[str, Type[Operation]] = {
        "add": Add,
        "subtract": Subtract,
        "multiply": Multiply,
        "divide": Divide,
        "integer_division": IntegerDivision,
        "percent": Percent,
        "power": Power,
        "root": Root,
        "modulus": Modulus,
        "absolute_diff": AbsoluteDiff,
    }

    @classmethod
    def create_operation(cls, op_name: str) -> Operation:
        """
        Instantiate an Operation by name (case-insensitive).

        Args:
            op_name: Name of operation (e.g. 'add', 'integer_division')

        Returns:
            Operation: An instance of the requested operation class

        Raises:
            OperationError: If the operation name is not registered
        """
        cleaned_name = op_name.strip().lower()
        op_cls = cls._operations.get(cleaned_name)
        if not op_cls:
            raise OperationError(f"Unsupported operation: '{op_name}'")
        return op_cls()

    @classmethod
    def list_operations(cls) -> List[str]:
        """Return the list of all available operation command names."""
        return list(cls._operations.keys())

    @classmethod
    def register_operation(cls, name: str, op_cls: Type[Operation]) -> None:
        """
        Dynamically register a new operation.

        Args:
            name: Operation command name
            op_cls: Operation subclass
        """
        cls._operations[name.strip().lower()] = op_cls
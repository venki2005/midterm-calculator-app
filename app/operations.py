from abc import ABC, abstractmethod
from decimal import Decimal


class Operation(ABC):
    @abstractmethod
    def execute(self, a: Decimal, b:Decimal) -> Decimal:
        """
        Execute calculation with 2 decimal numbers a & b
        """

class Addition(Operation):
    """
    Addition Operation implementation

    Perform addition of 2 numbers
    """

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        self.validate_operands(a,b)
        return a + b
    

class OperationFactory:
    """
    Factory class for creating operation instances.
    """
    _operations: dict[str, type] = {
        'add': Addition
        # 'subtract': Subtraction,
        # 'multiply': Multiplication,
        # 'divide': Division,
        # 'power': Power,
        # 'root': Root
    }

    @classmethod
    def register_operation(cls, name: str, operation_class: type) -> None:
        """
        Register a new operation type
        """

        if not issubclass(operation_class, Operation):
            raise TypeError("Operation class must inherit from Operation")
        cls._operations[name.lower()] = operation_class

    @classmethod
    def create_operation(cls, operation_type: str) -> Operation:
        """
        Register a new operation type
        """
    
        operation_class = cls._operation.get(operation_type.lower()) 
        if not operation_class:
            raise ValueError("Unknown Operation: {operation_type}")
        return operation_class()

    
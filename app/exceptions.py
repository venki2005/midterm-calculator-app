"""Any exceptions for calculator application."""

class CalculatorError(Exception):
    """Base exception for calculator errors."""

class ValidationError(CalculatorError):
    """Raised when user input fails numerical or boundary validation."""

class OperationError(CalculatorError):
    """Raised when an arithmetic or domain operation encounters an error."""
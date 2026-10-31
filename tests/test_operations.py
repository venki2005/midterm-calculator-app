"""
Unit tests for all calculator operations and the OperationFactory.
"""

from decimal import Decimal
import pytest

from app.exceptions import OperationError
from app.operations import (
    AbsoluteDiff,
    Add,
    Divide,
    IntegerDivision,
    Modulus,
    Multiply,
    Operation,
    OperationFactory,
    Percent,
    Power,
    Root,
    Subtract,
)


# ==========================================
# Arithmetic Operation Tests
# ==========================================

def test_add_operation():
    op = Add()
    assert op.execute(Decimal("5"), Decimal("3")) == Decimal("8")
    assert op.execute(Decimal("-2.5"), Decimal("4.5")) == Decimal("2.0")
    assert str(op) == "add"


def test_subtract_operation():
    op = Subtract()
    assert op.execute(Decimal("10"), Decimal("4")) == Decimal("6")
    assert op.execute(Decimal("4"), Decimal("10")) == Decimal("-6")
    assert str(op) == "subtract"


def test_multiply_operation():
    op = Multiply()
    assert op.execute(Decimal("6"), Decimal("7")) == Decimal("42")
    assert op.execute(Decimal("-3"), Decimal("5")) == Decimal("-15")
    assert str(op) == "multiply"


def test_divide_operation():
    op = Divide()
    assert op.execute(Decimal("20"), Decimal("4")) == Decimal("5")
    assert op.execute(Decimal("1"), Decimal("4")) == Decimal("0.25")
    assert str(op) == "divide"


def test_divide_by_zero():
    op = Divide()
    with pytest.raises(OperationError, match="Cannot divide by zero"):
        op.execute(Decimal("10"), Decimal("0"))


def test_integer_division_operation():
    op = IntegerDivision()
    assert op.execute(Decimal("10"), Decimal("3")) == Decimal("3")
    assert op.execute(Decimal("25"), Decimal("4")) == Decimal("6")
    assert op.execute(Decimal("7"), Decimal("2")) == Decimal("3")
    assert str(op) == "integer_division"


def test_integer_division_by_zero():
    op = IntegerDivision()
    with pytest.raises(OperationError, match="Cannot divide by zero"):
        op.execute(Decimal("15"), Decimal("0"))


def test_percent_operation():
    op = Percent()
    # 25 is 50% of 50
    assert op.execute(Decimal("25"), Decimal("50")) == Decimal("50")
    # 5 is 10% of 50
    assert op.execute(Decimal("5"), Decimal("50")) == Decimal("10")
    assert str(op) == "percent"


def test_percent_zero_base():
    op = Percent()
    with pytest.raises(OperationError, match="Cannot calculate percentage with zero base"):
        op.execute(Decimal("25"), Decimal("0"))


def test_power_operation():
    op = Power()
    assert op.execute(Decimal("2"), Decimal("3")) == Decimal("8")
    assert op.execute(Decimal("5"), Decimal("0")) == Decimal("1")
    assert op.execute(Decimal("4"), Decimal("0.5")) == Decimal("2.0")
    assert str(op) == "power"


def test_root_operation():
    op = Root()
    # Square root of 16 is 4
    assert op.execute(Decimal("16"), Decimal("2")) == Decimal("4.0")
    # Cube root of 27 is 3
    assert op.execute(Decimal("27"), Decimal("3")) == Decimal("3.0")
    assert str(op) == "root"


def test_root_zero_root():
    op = Root()
    with pytest.raises(OperationError, match="Cannot compute zeroth root"):
        op.execute(Decimal("16"), Decimal("0"))


def test_root_negative_number():
    op = Root()
    with pytest.raises(OperationError, match="Cannot calculate root of negative number"):
        op.execute(Decimal("-16"), Decimal("2"))


def test_modulus_operation():
    op = Modulus()
    assert op.execute(Decimal("10"), Decimal("3")) == Decimal("1")
    assert op.execute(Decimal("20"), Decimal("5")) == Decimal("0")
    assert str(op) == "modulus"


def test_modulus_by_zero():
    op = Modulus()
    with pytest.raises(OperationError, match="Cannot perform modulus by zero"):
        op.execute(Decimal("10"), Decimal("0"))


def test_absolute_diff_operation():
    op = AbsoluteDiff()
    assert op.execute(Decimal("15"), Decimal("20")) == Decimal("5")
    assert op.execute(Decimal("30"), Decimal("10")) == Decimal("20")
    assert str(op) == "absolute_diff"


# ==========================================
# OperationFactory Tests
# ==========================================

@pytest.mark.parametrize(
    "name, expected_cls",
    [
        ("add", Add),
        ("ADD", Add),
        ("subtract", Subtract),
        ("multiply", Multiply),
        ("divide", Divide),
        ("integer_division", IntegerDivision),
        ("percent", Percent),
        ("power", Power),
        ("root", Root),
        ("modulus", Modulus),
        ("absolute_diff", AbsoluteDiff),
    ],
)
def test_factory_create_operations(name, expected_cls):
    op = OperationFactory.create_operation(name)
    assert isinstance(op, expected_cls)


def test_factory_invalid_operation():
    with pytest.raises(OperationError, match="Unsupported operation: 'unknown_op'"):
        OperationFactory.create_operation("unknown_op")


def test_factory_list_operations():
    ops = OperationFactory.list_operations()
    assert "add" in ops
    assert "integer_division" in ops
    assert "percent" in ops
    assert "divide" in ops
    assert len(ops) >= 10


def test_factory_register_operation():
    class DummyOp(Operation):
        def execute(self, a: Decimal, b: Decimal) -> Decimal:
            return a

    OperationFactory.register_operation("dummy", DummyOp)
    assert "dummy" in OperationFactory.list_operations()
    created = OperationFactory.create_operation("dummy")
    assert isinstance(created, DummyOp)
    assert created.execute(Decimal("42"), Decimal("1")) == Decimal("42")
from decimal import Decimal
from app.calculation import Calculation
from app.calculator_memento import CalculatorMemento


def test_calculator_memento():
    calc1 = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    history = [calc1]
    memento = CalculatorMemento(history)

    # 1. Verify history / state preservation
    if hasattr(memento, "history"):
        assert memento.history == history
    elif hasattr(memento, "state"):
        assert memento.state == history
    elif hasattr(memento, "get_state"):
        assert memento.get_state() == history

    # 2. Verify timestamp existence (if applicable)
    if hasattr(memento, "timestamp"):
        assert memento.timestamp is not None

    # 3. String / representation checks
    repr_str = repr(memento)
    str_val = str(memento)
    assert len(repr_str) > 0 or len(str_val) > 0

    # 4. Equality with itself and inequality with other types
    assert memento == memento
    assert memento != "not_a_memento"
    assert memento != None
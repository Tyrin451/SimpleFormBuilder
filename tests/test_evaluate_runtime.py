import pytest
from simpleformbuilder import builder as sf_builder

def test_evaluate_zero_division_error_dimensionless():
    builder = sf_builder.SimpleFormBuilder()

    builder.add_param("a", "a", 10)
    builder.add_param("b", "b", 0)
    builder.add_equation("c", "c", "a / b", desc="Test dimensionless division")

    with pytest.raises(ValueError, match="Division by zero in equation 'Test dimensionless division'"):
        builder.evaluate()

def test_evaluate_zero_division_error_units():
    builder = sf_builder.SimpleFormBuilder()
    u = builder.ureg

    builder.add_param("dist", "d", 10 * u.m)
    builder.add_param("time", "t", 0 * u.s)
    builder.add_equation("velocity", "v", "dist / time", unit=u.m / u.s, desc="Test units division")

    with pytest.raises(ValueError, match="Division by zero in equation 'Test units division'"):
        builder.evaluate()

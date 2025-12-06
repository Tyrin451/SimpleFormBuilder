
import pytest
import pandas as pd
import numpy as np
import pint
from simpleformbuilder.builder import SimpleFormBuilder

def test_lambdify_simple_param():
    builder = SimpleFormBuilder()
    ureg = builder.ureg
    builder.add_param("a", "a", 10)
    builder.add_equation("eq1", "x", "a * 2")
    
    # Manually trigger evaluation to populate params if needed (though add_equation just registers)
    # Actually builder.evaluate() is needed to compute 'eq1' result in params, 
    # but lambdify should work on the expression string regardless of whether it was evaluated yet, 
    # AS LONG AS dependencies are resolvable at runtime (when func is called).
    
    func = builder.lambdify_equation("eq1")
    
    # Case 1: 'a' is not in DF, should use builder param
    df = pd.DataFrame({"dummy": [1, 2]})
    res = func(df)
    # Expect constant 20
    assert np.all(res == 20)

    # Case 2: 'a' is in DF, should use DF
    df2 = pd.DataFrame({"a": [1, 2, 3]})
    res2 = func(df2)
    assert np.array_equal(res2, [2, 4, 6])

def test_lambdify_units():
    builder = SimpleFormBuilder()
    ureg = builder.ureg
    builder.add_param("L", "L", 2 * ureg.meter)
    builder.add_equation("area", "A", "L**2")
    
    func = builder.lambdify_equation("area")
    
    df = pd.DataFrame({"id": [1]})
    res = func(df)
    
    # Result should have units
    assert isinstance(res, pint.Quantity) or (hasattr(res, "units") and res.units == ureg.meter**2)
    assert res.magnitude == 4

def test_lambdify_dataframe_units():
    builder = SimpleFormBuilder()
    ureg = builder.ureg
    # Equation: F = m * a
    builder.add_equation("F", "F", "m * a")
    
    func = builder.lambdify_equation("F")
    
    m_data = [10, 20] * ureg.kg
    a_data = [9.81, 9.81] * ureg.meter / ureg.second**2
    
    # Use list() to force pandas to create object-dtype column containing Quantity scalars,
    # preventing it from stripping units by converting to numpy float array.
    df = pd.DataFrame({
        "m": list(m_data),
        "a": list(a_data)
    })
    
    res = func(df)
    # Check shape and units
    assert len(res) == 2
    # If using standard pandas with object-dtype quantities, the result is a Series of Quantities.
    # It does NOT have a .units attribute on the Series/array itself.
    # We must check the elements.
    if hasattr(res, "units"):
        assert res.dimensionality == ureg.newton.dimensionality
        # Or convert to newton to be sure
        assert res.to("newton").units == ureg.newton
    else:
        # Assume iterable of quantities (Series or Array)
        val0 = res.iloc[0] if hasattr(res, 'iloc') else res[0]
        assert val0.dimensionality == ureg.newton.dimensionality
        val_newton = val0.to("newton")
        assert np.isclose(val_newton.magnitude, 98.1)

def test_lambdify_missing_var():
    builder = SimpleFormBuilder()
    builder.add_equation("eq", "y", "x * 2") # x is unknown
    
    func = builder.lambdify_equation("eq")
    
    df = pd.DataFrame({"z": [1]})
    
    # Should raise error because 'x' is neither in DF nor params
    with pytest.raises(KeyError, match="x"):
        func(df)

def test_lambdify_dependency_chain():
    """
    Test user warning: equation depends on result of another function.
    """
    builder = SimpleFormBuilder()
    builder.add_param("x", "x", 5)
    builder.add_equation("y", "y", "x + 2") # y = 7
    builder.add_equation("z", "z", "y * 3") # z = 21
    
    # Must evaluate to populate params['y'] if we rely on fallback
    builder.evaluate() 
    
    func = builder.lambdify_equation("z")
    
    # 1. Use internal intermediate result
    df = pd.DataFrame({"dummy": [0]})
    res = func(df)
    # Result might be scalar if no input was array
    if np.ndim(res) == 0:
        assert res == 21
    else:
        assert res[0] == 21
    
    # 2. Override intermediate result
    df2 = pd.DataFrame({"y": [10]})
    res2 = func(df2)
    # z = y * 3 = 10 * 3 = 30
    if np.ndim(res2) == 0:
        assert res2 == 30
    else:
        # If input was dataframe col (Series), result is Series
        assert res2.iloc[0] == 30 if hasattr(res2, 'iloc') else res2[0] == 30


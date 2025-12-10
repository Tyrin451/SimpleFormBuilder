import pytest
from simpleformbuilder import builder
import numpy as np
import pint

def test_chained_evaluation_lambdify():
    """
    Test that lambdify_equation correctly expands dependencies (chained evaluation).
    Also tests that it handles input units correctly (no double application).
    """
    sf = builder.SimpleFormBuilder()

    # Define parameters and equations similar to the reproduction case
    sf.add_param("F", "F", 1000 * sf.ureg.newton)
    sf.add_param("S", "S", 10 * sf.ureg.cm**2)
    sf.add_param("Re", "R_e", 200 * sf.ureg.MPa)

    # 1. sigma = F / S (MPa)
    sf.add_equation("sigma", "\\sigma", "F / S", unit=sf.ureg.MPa)
    
    # 2. sigma_a = Re / 2 (MPa)
    sf.add_equation("sigma_a", "\\sigma_a", "Re / 2", unit=sf.ureg.MPa)
    
    # 3. TC = sigma / sigma_a (dimensionless)
    sf.add_equation("TC", "TC", "sigma / sigma_a")

    # Compile the function for TC
    TC_func = sf.lambdify_equation("TC")

    # Test with different values than defaults
    # F = 2000 N -> sigma = 2 MPa
    # Re = 200 MPa -> sigma_a = 100 MPa
    # TC = 2 / 100 = 0.02
    
    inputs = {
        "F": 2000 * sf.ureg.newton,
        "S": 10 * sf.ureg.cm**2,
        "Re": 200 * sf.ureg.MPa
    }
    
    result = TC_func(inputs)
    
    # Check value
    assert result == pytest.approx(0.02)
    
    # Check dimensionless
    if isinstance(result, pint.Quantity):
        assert result.dimensionless

def test_chained_evaluation_no_units_input():
    """
    Test chained evaluation where inputs are plain numbers (magnitude), relying on params units.
    """
    sf = builder.SimpleFormBuilder()
    sf.add_param("A", "A", 1 * sf.ureg.meter)
    sf.add_param("B", "B", 2 * sf.ureg.meter)
    
    # C = A + B
    sf.add_equation("C", "C", "A + B", unit=sf.ureg.meter)
    
    # D = C * 2
    sf.add_equation("D", "D", "C * 2", unit=sf.ureg.meter)
    
    D_func = sf.lambdify_equation("D")
    
    # Inputs as plain numbers (magnitudes assumed in base units defined in params)
    inputs = {"A": 10, "B": 20} # 10m, 20m -> C=30m -> D=60m
    
    result = D_func(inputs)
    
    assert result.magnitude == pytest.approx(60)
    assert result.units == sf.ureg.meter

import pytest
import pint
from builder import SimpleFormBuilder

def test_nominal_workflow():
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("Fx", "F_x", 10 * u.kN, desc="Force axiale")
    builder.add_param("A", "A", 50 * u.cm**2, desc="Section")
    
    builder.add_equation("sigma", "\\sigma", "Fx / A", unit=u.MPa, desc="Contrainte")
    
    builder.evaluate()
    
    assert builder.params["sigma"].magnitude == pytest.approx(2.0)
    assert builder.params["sigma"].units == u.MPa
    
    report = builder.report()
    assert "F_x" in report
    # Pint might use \mathrm or \text depending on version/config. 
    # Let's check for the number and the unit string loosely or adjust to what we observed.
    # Observed: \mathrm{MPa}
    assert "10.00" in report
    assert "kN" in report 
    assert "\\sigma" in report
    assert "2.00" in report
    assert "MPa" in report

def test_unit_conversion():
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("L1", "L_1", 10 * u.m)
    builder.add_param("L2", "L_2", 50 * u.cm)
    
    builder.add_equation("L_total", "L_{tot}", "L1 + L2", unit=u.m)
    
    builder.evaluate()
    
    assert builder.params["L_total"].magnitude == pytest.approx(10.5)
    assert builder.params["L_total"].units == u.m

def test_math_functions():
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("x", "x", 9)
    builder.add_equation("y", "y", "sqrt(x)")
    
    builder.evaluate()
    assert builder.params["y"] == pytest.approx(3.0)

def test_checks():
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("sigma", "\\sigma", 150 * u.MPa)
    builder.add_param("fy", "f_y", 235 * u.MPa)
    
    builder.add_check("sigma < fy", desc="Check yield")
    builder.add_check("sigma > fy", desc="Check fail")
    
    builder.evaluate()
    
    report = builder.report()
    assert "\\textbf{\\textcolor{green}{OK}}" in report
    assert "\\textbf{\\textcolor{red}{FAIL}}" in report

def test_hidden_variables():
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("hidden_val", "H", 10, hidden=True)
    builder.add_equation("visible_val", "V", "hidden_val * 2")
    
    builder.evaluate()
    
    report = builder.report()
    # Hidden variable symbol 'H' should not be in report
    assert "H &=" not in report 
    # Visible variable symbol 'V' should be in report
    assert "V" in report
    assert "20" in report

def test_formatting():
    builder = SimpleFormBuilder()
    builder.add_param("pi_val", "\\pi", 3.14159265, fmt=".4f")
    builder.evaluate()
    report = builder.report()
    assert "3.1416" in report

def test_engineering_functions():
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("val1", "v1", -10)
    builder.add_param("val2", "v2", 20)
    
    builder.add_equation("abs_val", "abs_v", "abs(val1)")
    builder.add_equation("min_val", "min_v", "min(val1, val2)")
    builder.add_equation("max_val", "max_v", "max(val1, val2)")
    
    builder.evaluate()
    
    assert builder.params["abs_val"] == 10
    assert builder.params["min_val"] == -10
    assert builder.params["max_val"] == 20

def test_advanced_unit_conversions():
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    # Area conversion
    builder.add_param("width", "w", 100 * u.cm)
    builder.add_param("height", "h", 2 * u.m)
    builder.add_equation("area", "A", "width * height", unit=u.m**2)
    
    # Mixed units in min/max (requires compatible units)
    builder.add_param("force1", "F1", 1 * u.kN)
    builder.add_param("force2", "F2", 500 * u.N)
    
    builder.add_equation("max_force", "F_{max}", "max(force1, force2)", unit=u.kN)
    
    builder.evaluate()
    
    assert builder.params["area"].magnitude == pytest.approx(2.0)
    assert builder.params["area"].units == u.m**2
    
    assert builder.params["max_force"].magnitude == pytest.approx(1.0)
    assert builder.params["max_force"].units == u.kN

import pytest
import pint
from simpleformbuilder import builder as sf_builder

def test_nominal_workflow():
    builder = sf_builder.SimpleFormBuilder()
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
    builder = sf_builder.SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("L1", "L_1", 10 * u.m)
    builder.add_param("L2", "L_2", 50 * u.cm)
    
    builder.add_equation("L_total", "L_{tot}", "L1 + L2", unit=u.m)
    
    builder.evaluate()
    
    assert builder.params["L_total"].magnitude == pytest.approx(10.5)
    assert builder.params["L_total"].units == u.m

def test_math_functions():
    builder = sf_builder.SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("x", "x", 9)
    builder.add_equation("y", "y", "sqrt(x)")
    
    builder.evaluate()
    assert builder.params["y"] == pytest.approx(3.0)

def test_checks():
    builder = sf_builder.SimpleFormBuilder()
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
    builder = sf_builder.SimpleFormBuilder()
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
    builder = sf_builder.SimpleFormBuilder()
    builder.add_param("pi_val", "\\pi", 3.14159265, fmt=".4f")
    builder.evaluate()
    report = builder.report()
    assert "3.1416" in report

def test_engineering_functions():
    builder = sf_builder.SimpleFormBuilder()
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
    builder = sf_builder.SimpleFormBuilder()
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

def test_latex_rendering():
    builder = sf_builder.SimpleFormBuilder()
    u = builder.ureg
    
    # Test case from issue: N + T / mu
    # 'N' clashes with sympy.N (numerical evaluation)
    # 'mu' needs to be rendered as \mu
    
    builder.add_param("N", "N_{max}", 100 * u.N)
    builder.add_param("T", "T_{max}", 50 * u.N)
    builder.add_param("mu", r"\mu", 0.2)
    
    builder.add_equation("F0", "F_0", "N + T/mu", unit=u.N)
    
    builder.evaluate()
    
    report = builder.report()
    
    # Check for correct latex rendering
    # Expected: F_0 &= N_{max} + \frac{T_{max}}{\mu}
    # We check for parts of it to be robust against spacing changes
    assert r"N_{max}" in report
    assert r"\frac{T_{max}}{\mu}" in report
    assert r"\mu" in report

def test_getitem_access():
    builder = sf_builder.SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("sigma", "\\sigma", 100 * u.MPa)
    builder.add_equation("force", "F", "sigma * 2 * u.cm**2", unit=u.N)
    
    builder.evaluate()
    
    # Test access to param
    assert builder["sigma"] == 100 * u.MPa
    
    # Test access to equation result
    # 100 MPa * 2 cm^2 = 100 N/mm^2 * 200 mm^2 = 20000 N = 20 kN
    # 100 * 10^6 Pa * 2 * (10^-2 m)^2 = 100 * 10^6 * 2 * 10^-4 = 200 * 10^2 = 20000 N
    assert builder["force"].magnitude == pytest.approx(20000)
    assert builder["force"].units == u.N
    
    # Test KeyError
    with pytest.raises(KeyError):
        _ = builder["non_existent"]

def test_check_formatting():
    builder = sf_builder.SimpleFormBuilder()
    
    # Param with default format
    builder.add_param("val", "v", 0.123456)
    # Param with custom format
    builder.add_param("percent", "p", 0.123456, fmt=".2%")
    
    # Check using default format of variable
    builder.add_check("val < 1", "Default check")
    # Check overriding format
    builder.add_check("val < 1", "Custom check", fmt=".4f")
    # Check using percent format
    builder.add_check("percent < 1", "Percent check")
    
    builder.evaluate()
    report = builder.report()
    
    # Default precision is 2, so 0.12
    assert "0.12" in report
    
    # Custom check should show 0.1235
    assert "0.1235" in report
    
    # Percent check should show 12.35%
    assert "12.35%" in report



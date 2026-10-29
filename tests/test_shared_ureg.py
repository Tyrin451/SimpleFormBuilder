import pytest
import pint
from simpleformbuilder.builder import SimpleFormBuilder, _default_ureg

def test_shared_ureg_default():
    """Test that two standard instances share the same UnitRegistry."""
    form1 = SimpleFormBuilder()
    form2 = SimpleFormBuilder()

    assert form1.ureg is form2.ureg
    assert form1.ureg is _default_ureg

def test_evaluate_cross_instance_quantities():
    """Test evaluating quantities across different instances using the default shared registry."""
    form1 = SimpleFormBuilder()
    u = form1.ureg
    form1.add_param("F", "F", 100 * u.N, "Force")
    form1.evaluate()

    form2 = SimpleFormBuilder()
    # Use result from form1 directly in form2
    form2.add_param("F_in", "F_{in}", form1.params["F"], "Force from form1")
    form2.add_param("A", "A", 2 * u.m**2, "Area")
    form2.add_equation("P", "P", "F_in / A", unit=u.Pa, desc="Pressure")

    # Should evaluate without registry mismatch errors
    form2.evaluate()

    assert form2.params["P"].magnitude == 50
    assert str(form2.params["P"].units) == "pascal"

def test_custom_ureg():
    """Test that providing a custom UnitRegistry isolates the instance."""
    custom_ureg = pint.UnitRegistry()
    form1 = SimpleFormBuilder(ureg=custom_ureg)
    form2 = SimpleFormBuilder()

    assert form1.ureg is custom_ureg
    assert form1.ureg is not form2.ureg
    assert form1.ureg is not _default_ureg

    u1 = form1.ureg
    form1.add_param("F", "F", 100 * u1.N, "Force")
    form1.evaluate()

    # Using result from form1 in form2 should raise a DimensionalityError/ValueError due to registry mismatch
    form2.add_param("F_in", "F_{in}", form1.params["F"], "Force from form1")
    form2.add_param("A", "A", 2 * form2.ureg.m**2, "Area")
    form2.add_equation("P", "P", "F_in / A", unit=form2.ureg.Pa, desc="Pressure")

    with pytest.raises(Exception):
        form2.evaluate()

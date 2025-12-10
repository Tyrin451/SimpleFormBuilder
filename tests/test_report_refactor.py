
import pytest
from simpleformbuilder import builder as sf_builder

def test_report_environment_override():
    """Verify strictly environment override behavior."""
    builder = sf_builder.SimpleFormBuilder(template="detailed")
    # "detailed" template uses "itemize" by default for all steps
    
    builder.add_param("x", "x", 10)
    builder.add_equation("y", "y", "x * 2")
    
    builder.evaluate()
    
    # 1. Default behavior (template default)
    report_default = builder.report()
    assert "itemize" in report_default
    assert "align*" not in report_default
    
    # 2. Strict override
    report_override = builder.report(environment="align*")
    assert "itemize" not in report_override
    assert "align*" in report_override
    
    # 3. Explicit None (should also be default)
    report_none = builder.report(environment=None)
    assert "itemize" in report_none
    
def test_report_formatting_helpers():
    """Verify extracted helpers work implicitly through report generation."""
    builder = sf_builder.SimpleFormBuilder()
    builder.add_param("x", "x", 10)
    builder.evaluate()
    
    report = builder.report()
    assert "10.00" in report # precision default 2

if __name__ == "__main__":
    test_report_environment_override()
    test_report_formatting_helpers()

import pytest
import pint
from simpleformbuilder import builder as sf_builder

def test_param_name_validation():
    builder = sf_builder.SimpleFormBuilder()
    u = builder.ureg
    
    # Valid
    builder.add_param("valid_param", "v_p", 1)
    
    # Invalid starts with number
    with pytest.raises(ValueError, match="must be a valid Python identifier"):
        builder.add_param("1invalid", "inv", 1)
        
    # Invalid spaces
    with pytest.raises(ValueError, match="must be a valid Python identifier"):
        builder.add_param("invalid param", "inv", 1)
        
    # Invalid chars
    with pytest.raises(ValueError, match="must be a valid Python identifier"):
        builder.add_param("param-invalid", "inv", 1)

def test_param_type_validation():
    builder = sf_builder.SimpleFormBuilder()
    u = builder.ureg
    
    # Valid types
    builder.add_param("p1", "p1", 1)
    builder.add_param("p2", "p2", 1.0)
    builder.add_param("p3", "p3", 1 * u.m)
    import numpy as np
    builder.add_param("p4", "p4", np.array([1, 2]))
    
    # Invalid types
    with pytest.raises(TypeError, match="must be an int, float, pint.Quantity, or np.ndarray"):
        builder.add_param("bad_param", "b", "string_value")
        
    with pytest.raises(TypeError):
        builder.add_param("bad_param2", "b", {"a": 1})

def test_equation_validation():
    builder = sf_builder.SimpleFormBuilder()
    
    # Valid
    builder.add_param("x", "x", 10)
    builder.add_equation("y", "y", "x * 2")
    
    # Invalid name
    with pytest.raises(ValueError, match="must be a valid Python identifier"):
        builder.add_equation("1y", "y", "x * 2")
        
    # Forbidden keywords (security check)
    with pytest.raises(ValueError, match="contains forbidden keywords"):
        builder.add_equation("bad", "b", "eval('os.system')")
        
    with pytest.raises(ValueError, match="contains forbidden substring '__'"):
        builder.add_equation("bad2", "b", "__import__('os')")

def test_check_validation():
    builder = sf_builder.SimpleFormBuilder()
    builder.add_param("x", "x", 10)
    
    # Valid
    builder.add_check("x > 5", "Check x")
    
    # Forbidden
    with pytest.raises(ValueError, match="contains forbidden keywords"):
        builder.add_check("import os", "Bad check")

def test_lambdify_resolution_docs():
    """
    Verifies that the docstring for lambdify_equation explains the mechanisms.
    """
    ds = sf_builder.SimpleFormBuilder.lambdify_equation.__doc__
    assert "Variable Resolution Priority" in ds
    assert "Unit Injection" in ds
    assert "DataFrame/Input Dict" in ds

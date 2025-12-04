
import pytest
import numpy as np
from simpleformbuilder import builder as sf_builder

def test_numpy_params():
    builder = sf_builder.SimpleFormBuilder()
    v = np.array([1, 2, 3])
    builder.add_param("v", "v", v)
    assert np.array_equal(builder.params["v"], v)

def test_numpy_check_all_explicit():
    builder = sf_builder.SimpleFormBuilder()
    v1 = np.array([10, 20, 30])
    v2 = np.array([5, 15, 25])
    builder.add_param("v1", "v_1", v1)
    builder.add_param("v2", "v_2", v2)
    
    # explicit all()
    builder.add_check("all(v1 > v2)", desc="All greater")
    builder.evaluate()
    assert builder.steps[-1]["result"] == True

def test_numpy_check_implicit_all():
    builder = sf_builder.SimpleFormBuilder()
    v1 = np.array([10, 20, 30])
    v2 = np.array([5, 15, 25])
    builder.add_param("v1", "v_1", v1)
    builder.add_param("v2", "v_2", v2)
    
    # implicit all via array result handling
    builder.add_check("v1 > v2", desc="All greater implicit")
    builder.evaluate()
    assert builder.steps[-1]["result"] == True

def test_numpy_check_fail():
    builder = sf_builder.SimpleFormBuilder()
    v1 = np.array([10, 20, 30])
    v2 = np.array([5, 25, 25]) # 20 < 25, so second element fails
    builder.add_param("v1", "v_1", v1)
    builder.add_param("v2", "v_2", v2)
    
    builder.add_check("v1 > v2", desc="Some greater")
    builder.evaluate()
    assert builder.steps[-1]["result"] == False

def test_numpy_equation():
    builder = sf_builder.SimpleFormBuilder()
    v = np.array([1, 2, 3])
    builder.add_param("v", "v", v)
    builder.add_equation("v2", "v^2", "v**2")
    builder.evaluate()
    
    expected = np.array([1, 4, 9])
    assert np.array_equal(builder.params["v2"], expected)

def test_report_numpy():
    builder = sf_builder.SimpleFormBuilder()
    v = np.array([1.1, 2.2])
    builder.add_param("v", "v", v)
    builder.evaluate()
    report = builder.report()
    assert "[1.1, 2.2]" in report or "[1.1, 2.2 ]" in report # spacing might vary

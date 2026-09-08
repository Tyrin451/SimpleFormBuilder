import pytest
import numpy as np
from simpleformbuilder.builder import SimpleFormBuilder
import pint

def test_conditional_equation_evaluation():
    builder = SimpleFormBuilder()
    builder.add_param("x", "x", 5)
    builder.add_conditional_equation("y", "y", "x > 0", "10", "20")

    builder.evaluate()
    assert builder.params["y"] == 10

    builder.update_param("x", -5)
    builder.evaluate()
    assert builder.params["y"] == 20

def test_conditional_equation_latex():
    builder = SimpleFormBuilder()
    builder.add_param("x", "x", 5)
    builder.add_conditional_equation("y", "y", "x > 0", "10", "20")
    report = builder.report()

    assert r"\begin{cases}" in report
    assert r"\text{si } x > 0" in report
    assert r"\text{sinon}" in report

def test_conditional_equation_lambdify_array():
    builder = SimpleFormBuilder()
    builder.add_param("a", "a", 2)
    builder.add_param("b", "b", 5)
    builder.add_conditional_equation("y", "y", "x > 0", "a*x + b", "b")

    # Needs to compile lambdify with NumPy.
    f = builder.lambdify_equation("y")

    import pandas as pd
    df = pd.DataFrame({"x": [1, -1, 0, 10]})
    result = f(df)

    np.testing.assert_array_equal(result, np.array([7, 5, 5, 25]))

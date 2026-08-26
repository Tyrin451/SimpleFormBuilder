import pytest
from simpleformbuilder.builder import SimpleFormBuilder
from simpleformbuilder.utils import SecurityError, security_check

def test_safe_parse_blocks_builtins():
    builder = SimpleFormBuilder()

    # Try to add an equation with a malicious expression
    with pytest.raises(SecurityError) as excinfo:
        builder.add_equation("vuln", "v", "__import__('os').system('echo VULN')")
    assert "forbidden" in str(excinfo.value)

def test_safe_parse_blocks_eval():
    builder = SimpleFormBuilder()

    with pytest.raises(SecurityError) as excinfo:
        builder.add_equation("vuln2", "v", "eval('print(1)')")
    assert "forbidden" in str(excinfo.value)

def test_report_blocks_security_error():
    builder = SimpleFormBuilder()
    # Bypass add_equation check just to test report logic (which handles checks)
    builder.graph.steps.append({
        "type": "check",
        "expr": "2 + / x",
        "desc": "vuln check"
    })

    with pytest.raises(SecurityError) as excinfo:
        builder.report()
    assert "Failed to safely parse" in str(excinfo.value)

def test_ast_security_allowed_expressions():
    # Valid math operations, comparisons, function calls, and units
    valid_exprs = [
        "a + b * c / 2.5",
        "sqrt(x**2 + y**2)",
        "min(a, b) + max(c, d)",
        "sin(x) + cos(y) + tan(z) + log(a) + exp(b) + abs(c)",
        "all(v1 > v2) and any(v3 <= v4)",
        "sigma * 2 * u.cm**2",
        "x >= 0 and y != 10 or not z",
    ]
    for expr in valid_exprs:
        security_check("test_eq", expr)

def test_ast_security_blocks_malicious():
    # Forbidden functions, attributes, statements, dunder attributes
    malicious_exprs = [
        "open('/etc/passwd')",
        "exec('import os')",
        "__import__('os').system('ls')",
        "x.__class__",
        "(lambda x: x)(10)",
        "getattr(obj, 'attr')",
        "sys.exit()",
        "builtins.print(1)",
        "x.attribute_access",
        "import os",
    ]
    for expr in malicious_exprs:
        with pytest.raises(SecurityError):
            security_check("test_eq", expr)

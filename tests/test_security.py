import pytest
from simpleformbuilder.builder import SimpleFormBuilder
from simpleformbuilder.utils import SecurityError

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

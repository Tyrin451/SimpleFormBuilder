import ast
import sympy
from sympy.parsing.sympy_parser import parse_expr

class SecurityError(ValueError):
    """Exception raised for security violations in expressions."""
    pass

ALLOWED_FUNCTIONS = {
    "sqrt", "sin", "cos", "tan", "log", "exp", "abs", "min", "max",
    "pi", "all", "any", "where"
}

FORBIDDEN_KEYWORDS = {
    "import", "lambda", "open", "eval", "exec", "compile", "input",
    "sys", "os", "globals", "locals", "builtins", "getattr", "setattr",
    "delattr", "__import__"
}

ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BoolOp,
    ast.Constant,
    ast.Name,
    ast.Call,
    ast.Attribute,
    ast.Load,
    # BinOp operators
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    # UnaryOp operators
    ast.UAdd, ast.USub, ast.Not,
    # Compare operators
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    # BoolOp operators
    ast.And, ast.Or,
)

def security_check(name, expr):
    # Sécurité et Robustesse : Validation des noms
    if not name.isidentifier():
        raise SecurityError(f"Equation name '{name}' must be a valid Python identifier.")

    # Check for double underscore substring
    if "__" in expr:
        raise SecurityError(f"Expression '{expr}' contains forbidden substring '__'.")

    # Parse expression into AST using mode='eval'
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise SecurityError(f"Expression '{expr}' contains forbidden keywords or invalid syntax: {e}")

    # Walk AST nodes
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise SecurityError(f"Expression '{expr}' contains forbidden syntax construct '{type(node).__name__}'.")

        # Check Identifier Names
        if isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id in FORBIDDEN_KEYWORDS:
                raise SecurityError(f"Expression '{expr}' contains forbidden keywords: '{node.id}'.")

        # Check Calls
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise SecurityError(f"Expression '{expr}' contains forbidden function call structure.")
            if node.func.id not in ALLOWED_FUNCTIONS:
                raise SecurityError(f"Expression '{expr}' contains forbidden keywords or function '{node.func.id}'.")

        # Check Attribute Access (only u.<unit> allowed)
        elif isinstance(node, ast.Attribute):
            if not (isinstance(node.value, ast.Name) and node.value.id == "u"):
                raise SecurityError(f"Expression '{expr}' contains forbidden attribute access '{node.attr}'.")
            if node.attr.startswith("__"):
                raise SecurityError(f"Expression '{expr}' contains forbidden attribute access '{node.attr}'.")

def safe_parse(expr_str, local_dict, evaluate=False):
    """
    Safely parses a string into a SymPy expression.
    Prevents arbitrary code execution by removing __builtins__.
    """
    global_dict = {"__builtins__": {}}

    # Inject safe sympy classes/functions into global_dict
    for k in dir(sympy):
        if not k.startswith("_"):
            global_dict[k] = getattr(sympy, k)

    try:
        return parse_expr(expr_str, local_dict=local_dict, global_dict=global_dict, evaluate=evaluate)
    except Exception as e:
        # Re-raise parsing errors explicitly to avoid silent fallbacks if it was a real parsing error
        raise SecurityError(f"Failed to safely parse expression '{expr_str}': {e}")

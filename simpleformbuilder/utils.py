import re
import sympy
from sympy.parsing.sympy_parser import parse_expr

class SecurityError(ValueError):
    """Exception raised for security violations in expressions."""
    pass

def security_check(name, expr):
    # Sécurité et Robustesse : Validation des noms
    if not name.isidentifier():
        raise SecurityError(f"Equation name '{name}' must be a valid Python identifier.")

    # Validation sécuritaire stricte sur l'expression (avant parsing)
    # On interdit les mots-clés dangereux et l'accès aux attributs privés
    forbidden = ["import", "lambda", "open", "eval", "exec", "compile", "input", "sys", "os", "globals", "locals", "builtins", "getattr", "setattr", "delattr"]

    # Check for double underscore separately (not necessarily a word)
    if "__" in expr:
        raise SecurityError(f"Expression '{expr}' contains forbidden substring '__'.")
            
    # Check for forbidden words
    pattern = r"\b(" + "|".join(forbidden) + r")\b"
    if re.search(pattern, expr):
        raise SecurityError(f"Expression '{expr}' contains forbidden keywords.")

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

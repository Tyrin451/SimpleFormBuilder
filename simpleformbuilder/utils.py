

def security_check(name, expr):
    # Sécurité et Robustesse : Validation des noms
    if not name.isidentifier():
        raise ValueError(f"Equation name '{name}' must be a valid Python identifier.")

    # Validation sécuritaire stricte sur l'expression (avant parsing)
    # On interdit les mots-clés dangereux et l'accès aux attributs privés
    # Use regex to avoid false positives (e.g. 'os' in 'cos')
    import re
    forbidden = ["import", "lambda", "open", "eval", "exec", "compile", "input", "sys", "os"]
    # Check for double underscore separately (not necessarily a word)
    if "__" in expr:
            raise ValueError(f"Expression '{expr}' contains forbidden substring '__'.")
            
    # Check for forbidden words
    pattern = r"\b(" + "|".join(forbidden) + r")\b"
    if re.search(pattern, expr):
            raise ValueError(f"Expression '{expr}' contains forbidden keywords.")
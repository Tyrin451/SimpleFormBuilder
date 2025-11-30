import sympy

def test_sub():
    expr_str = "sigma < sigma_a"
    sym_expr = sympy.sympify(expr_str, evaluate=False)
    
    # Simulate wrapping in braces
    replacements = {
        "sigma": r"{\sigma} (2.00)",
        "sigma_a": r"{\sigma_a} (100.00)" 
    }
    
    subs = {}
    for name, latex_str in replacements.items():
        subs[sympy.Symbol(name)] = sympy.Symbol(latex_str)
        
    subbed_expr = sym_expr.subs(subs)
    print(f"Latex: {sympy.latex(subbed_expr)}")

if __name__ == "__main__":
    test_sub()

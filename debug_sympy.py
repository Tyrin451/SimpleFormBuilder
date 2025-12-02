
import sympy
try:
    expr = sympy.sympify("all(v1 > v2)", evaluate=False)
    print(f"Type: {type(expr)}")
    print(f"Free symbols: {expr.free_symbols}")
    
    v1 = sympy.Symbol("v1")
    v2 = sympy.Symbol("v2")
    subs = {v1: sympy.Symbol("val1"), v2: sympy.Symbol("val2")}
    
    res = expr.subs(subs)
    print(f"Result: {res}")
    print(f"Latex: {sympy.latex(res)}")
except Exception as e:
    print(f"Error: {e}")

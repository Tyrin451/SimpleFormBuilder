# Reference: e:\10_PYTHON\DEV\pysimpleform\specifications.md
# This implementation strictly follows the specifications defined in the file above.

import pint
import sympy
import numpy as np
from typing import Any, Optional, List, Dict

class SimpleFormBuilder:
    """
    Builder pattern for creating physical calculation reports.
    """

    def __init__(self):
        """
        Initializes the builder with unit registry and data structures.
        """
        # 3.1 Initialisation
        self.ureg = pint.UnitRegistry()
        self.precision = 2  # Default precision
        self.params: Dict[str, Any] = {}
        self.symbols: Dict[str, str] = {}
        self.steps: List[Dict[str, Any]] = []

    def add_param(self, name: str, symbol: str, value: Any, desc: str = "", hidden: bool = False, fmt: str = None):
        """
        Registers a constant parameter.
        """
        # 5. Sécurité et Robustesse : Validation des noms
        if not name.isidentifier():
            raise ValueError(f"Parameter name '{name}' must be a valid Python identifier.")
        
        # 5. Sécurité et Robustesse : Gestion des types
        if not isinstance(value, (int, float, pint.Quantity, np.ndarray)):
             raise TypeError(f"Value for '{name}' must be int, float, pint.Quantity, or np.ndarray.")

        self.params[name] = value
        self.symbols[name] = symbol
        
        self.steps.append({
            "type": "param",
            "name": name,
            "symbol": symbol,
            "value": value,
            "desc": desc,
            "hidden": hidden,
            "fmt": fmt
        })

    def add_equation(self, name: str, symbol: str, expr: str, unit: Any = None, desc: str = "", hidden: bool = False, fmt: str = None):
        """
        Registers an equation to be calculated.
        """
        # 5. Sécurité et Robustesse : Validation des noms
        if not name.isidentifier():
            raise ValueError(f"Equation name '{name}' must be a valid Python identifier.")

        self.symbols[name] = symbol
        
        self.steps.append({
            "type": "eq",
            "name": name,
            "symbol": symbol,
            "expr": expr,
            "unit": unit,
            "desc": desc,
            "hidden": hidden,
            "fmt": fmt
        })

    def add_check(self, expr: str, desc: str, name: str = "Check", fmt: str = None):
        """
        Adds a validation step.
        """
        self.steps.append({
            "type": "check",
            "name": name,
            "expr": expr,
            "desc": desc,
            "fmt": fmt
        })

    def evaluate(self):
        """
        Executes all registered calculations sequentially.
        """
        # 3.2.4 evaluate - Contexte d'évaluation
        # Prepare evaluation context with standard math functions and current params
        import math
        
        context = {
            "sqrt": np.sqrt,
            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "pi": np.pi,
            "log": np.log,
            "exp": np.exp,
            "abs": abs,
            "min": min,
            "max": max,
            "all": all,
            "any": any,
            "u": self.ureg, # Access to units via 'u' (common convention)
            **self.params
        }

        for step in self.steps:
            if step["type"] == "eq":
                try:
                    # 3.2.4 evaluate - 2. Evaluer expr
                    result = eval(step["expr"], {"__builtins__": {}}, context)
                    
                    # 3.2.4 evaluate - 4. Conversion d'unité
                    if step["unit"]:
                        if isinstance(result, pint.Quantity):
                            result = result.to(step["unit"])
                        else:
                             # If result is scalar but unit is requested, assume it's that unit? 
                             # Or raise error? Spec says "converti dans cette unité".
                             # Usually implies result should be Quantity.
                             # Let's assume result is Quantity if units are involved.
                             # If result is just number, we might want to attach unit?
                             # Spec: "Si fournie, le résultat calculé doit être converti dans cette unité."
                             result = self.ureg.Quantity(result, step["unit"])

                    # 3.2.4 evaluate - 5. Stocker le résultat
                    self.params[step["name"]] = result
                    step["result"] = result
                    
                    # Update context for next steps
                    context[step["name"]] = result
                    
                except ZeroDivisionError:
                    raise ZeroDivisionError(f"Division by zero in equation '{step['name']}': {step['expr']}")
                except pint.DimensionalityError as e:
                    raise pint.DimensionalityError(e.units1, e.units2, e.extra_msg) from e
                except Exception as e:
                    raise RuntimeError(f"Error evaluating equation '{step['name']}': {e}")

            elif step["type"] == "check":
                try:
                    # 3.2.4 evaluate - 2. Evaluer expr (booléen)
                    result = eval(step["expr"], {"__builtins__": {}}, context)
                    
                    # Handle numpy array results
                    if isinstance(result, np.ndarray):
                        step["result"] = bool(result.all())
                    else:
                        step["result"] = result # Boolean
                except Exception as e:
                     raise RuntimeError(f"Error evaluating check '{step['desc']}': {e}")

    def lambdify_equation(self, name: str) -> Any:
        """
        Creates a function from the specified equation compatible with pandas.DataFrame.assign.
        
        The returned function accepts a DataFrame/dict. It resolves variables in the following order:
        1. From the provided DataFrame columns (if keys exist).
        2. From the builder's parameters/results (self.params).
        """
        # Find the equation step
        eq_step = None
        for step in self.steps:
            if step.get("type") == "eq" and step.get("name") == name:
                eq_step = step
                break
        
        if not eq_step:
            raise KeyError(f"Equation '{name}' not found.")
            
        expr_str = eq_step["expr"]
        
        # Parse expression to identify symbols
        # We use simple symbol extraction.
        # Note: we need to handle functions like sin/cos if present, but sympy.lambdify handles them.
        import sympy
        
        # Use existing context keys as potential symbols, plus any in expr 
        # (though ideally all variables should be in params/symbols)
        local_dict = {k: sympy.Symbol(k) for k in self.params.keys()}
        try:
             sym_expr = sympy.sympify(expr_str, locals=local_dict)
        except Exception as e:
             # Fallback: parse without locals (it might auto-detect symbols)
             sym_expr = sympy.sympify(expr_str)

        free_symbols = list(sym_expr.free_symbols)
        free_symbol_names = [str(s) for s in free_symbols]
        
        # Create lambdified function
        # We use 'numpy' as backend to support array operations
        # We include 'pint' awareness if possible? sympy.lambdify doesn't natively support pint.
        # But if we pass Pint arrays to a numpy-lambdified function, it usually works 
        # IF operations are standard (+, -, *, /) and numpy functions (np.sin).
        # We rely on user providing valid inputs.
        
        # Note: we must map symbols to arguments.
        f = sympy.lambdify(free_symbols, sym_expr, modules=["numpy", "math"])
        
        def wrapper(df):
            # df can be DataFrame or dict-like
            args = []
            for name in free_symbol_names:
                if name in df:
                    # Use .values to get numpy array, avoiding issues with 
                    # pandas Series * pint Quantity (which can fail broadcasting)
                    val = df[name]
                    if hasattr(val, "values"):
                        val = val.values
                    args.append(val)
                elif name in self.params:
                    args.append(self.params[name])
                else:
                    raise KeyError(f"Variable '{name}' required for equation '{expr_str}' not found in DataFrame or Builder parameters.")
            return f(*args)
            
        return wrapper

    def __getitem__(self, key: str) -> Any:
        """
        Allows dictionary-style access to parameters and results.
        """
        return self.params[key]

    def report(self, row_templates: Optional[Dict[str, str]] = None) -> str:
        """
        Generates the LaTeX report.
        
        Args:
            row_templates: Optional dictionary to override default row templates.
                           Keys: 'param', 'eq', 'check'.
        """
        default_templates = {
            "param": r"{symbol} &= {value} && \text{{{desc}}} \\",
            "eq": r"{symbol} &= {expr} = {value} && \text{{{desc}}} \\",
            "check": r"\text{{{name}}} : &&& \text{{{desc}}} \\ & {expr} \rightarrow {status} &&  \\"
        }
        
        templates = default_templates.copy()
        if row_templates:
            templates.update(row_templates)

        lines = [r"\begin{align*}"]

        # Helper to format value
        def format_value(val, fmt_spec):
            if fmt_spec:
                f_str = f"{{:{fmt_spec}}}"
            else:
                f_str = f"{{:.{self.precision}f}}"
            if isinstance(val, pint.Quantity):
                mag = val.magnitude
                # Format magnitude
                if isinstance(mag, np.ndarray):
                    #  mag_str = np.array2string(mag, precision=self.precision, separator=', ')
                    mag_str = r'\begin{bmatrix}' + np.array2string(mag, precision=self.precision, separator=r'\\', formatter={'float_kind' : lambda x : f_str.format(x)}).strip("[]") + r'\end{bmatrix}'
                else:
                    mag_str = f_str.format(mag)
                # Format unit (using pint's latex support or simple string)
                unit_str = rf"\ {val.units:~L}" # ~L for compact latex
                return f"{mag_str}{unit_str}".replace("%", r"\%")
            elif isinstance(val, (int, float)):
                return f_str.format(val).replace("%", r"\%")
            elif isinstance(val, np.ndarray):
                return np.array2string(val, 
                    precision=self.precision, 
                    separator=', ', 
                    formatter={'float_kind' : lambda x : f_str.format(x)})
            else:
                return str(val)

        # Helper to format expression to LaTeX
        def format_expr(expr_str):
            # Use sympy to parse and convert to latex
            # We need to substitute variable names with their latex symbols
            try:
                # Create locals dict to prevent sympy from interpreting params as functions (e.g. N)
                local_dict = {name: sympy.Symbol(name) for name in self.params.keys()}
                
                sym_expr = sympy.sympify(expr_str, locals=local_dict, evaluate=False)
                
                # Create a symbol_names dict for latex generation
                # This maps Symbol objects to their latex string representation
                symbol_names = {sympy.Symbol(name): sym for name, sym in self.symbols.items()}
                
                return sympy.latex(sym_expr, symbol_names=symbol_names)
            except Exception as e:
                # Fallback if parsing fails
                return expr_str.replace("**", "^").replace("*", r"\cdot ")
        
        for step in self.steps:
            if step.get("hidden", False):
                continue
            
            data = {
                "symbol": step.get("symbol", ""),
                "name": step.get("name", ""),
                "desc": step.get("desc", ""),
                "value": "",
                "expr": "",
                "status": ""
            }

            if step["type"] == "param":
                data["value"] = format_value(step["value"], step.get("fmt"))
                
            elif step["type"] == "eq":
                data["value"] = format_value(step.get("result"), step.get("fmt"))
                data["expr"] = format_expr(step["expr"])
                
            elif step["type"] == "check":
                data["status"] = r"\textbf{\textcolor{green}{OK}}" if step.get("result") else r"\textbf{\textcolor{red}{NOK}}"
                
                # Format expression with values
                try:
                    # Create locals dict
                    local_dict = {name: sympy.Symbol(name) for name in self.params.keys()}
                    
                    sym_expr = sympy.sympify(step["expr"], locals=local_dict, evaluate=False)
                    if not step.get("result"):
                        sym_expr = sympy.Not(sym_expr)
                    subs = {}
                    for sym in sym_expr.free_symbols:
                        sym_name = str(sym)
                        if sym_name in self.params:
                            val = self.params[sym_name]
                            latex_sym = self.symbols.get(sym_name, sym_name)
                            
                            # Priority: check step fmt > variable step fmt > default
                            fmt = step.get("fmt")
                            if fmt is None:
                                for s in self.steps:
                                    if s.get("name") == sym_name:
                                        fmt = s.get("fmt")
                                        break
                            
                            val_str = format_value(val, fmt)
                            new_sym_latex = rf"{{{latex_sym}}} = {val_str}"
                            subs[sym] = sympy.Symbol(new_sym_latex)
                    
                    data["expr"] = sympy.latex(sym_expr.subs(subs))
                except Exception as e:
                    print(f"Error formatting check expression: {e}")
                    data["expr"] = format_expr(step["expr"])

            try:
                line = templates[step["type"]].format(**data)
                lines.append(line)
            except KeyError:
                pass
            except Exception as e:
                lines.append(f"% Error rendering step {step.get('name')}: {e}")

        lines.append(r"\end{align*}")
        return "\n".join(lines)

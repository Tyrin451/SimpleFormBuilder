# Reference: e:\10_PYTHON\DEV\pysimpleform\specifications.md
# This implementation strictly follows the specifications defined in the file above.

import pint
import sympy
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
        if not isinstance(value, (int, float, pint.Quantity)):
             raise TypeError(f"Value for '{name}' must be int, float, or pint.Quantity.")

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

    def add_check(self, expr: str, desc: str, name: str = "Check"):
        """
        Adds a validation step.
        """
        self.steps.append({
            "type": "check",
            "name": name,
            "expr": expr,
            "desc": desc
        })

    def evaluate(self):
        """
        Executes all registered calculations sequentially.
        """
        # 3.2.4 evaluate - Contexte d'évaluation
        # Prepare evaluation context with standard math functions and current params
        import math
        import numpy as np # Optional but recommended in spec
        
        context = {
            "sqrt": np.sqrt,
            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "pi": np.pi,
            "log": np.log,
            "exp": np.exp,
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
                    step["result"] = result # Boolean
                except Exception as e:
                     raise RuntimeError(f"Error evaluating check '{step['desc']}': {e}")

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
            "check": r"\text{{{name}}} &: {expr} \rightarrow {status} && \text{{{desc}}} \\"
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
                mag_str = f_str.format(mag)
                # Format unit (using pint's latex support or simple string)
                unit_str = rf"\ {val.units:~L}" # ~L for compact latex
                return f"{mag_str}{unit_str}"
            elif isinstance(val, (int, float)):
                return f_str.format(val)
            else:
                return str(val)

        # Helper to format expression to LaTeX
        def format_expr(expr_str):
            # Use sympy to parse and convert to latex
            # We need to substitute variable names with their latex symbols
            try:
                sym_expr = sympy.sympify(expr_str, evaluate=False)
                # Create a substitution dict
                subs = {sympy.Symbol(name): sympy.Symbol(sym) for name, sym in self.symbols.items()}
                # Substitute
                sym_expr_sub = sym_expr.subs(subs)
                return sympy.latex(sym_expr_sub)
            except:
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
                data["status"] = r"\textbf{\textcolor{green}{OK}}" if step.get("result") else r"\textbf{\textcolor{red}{FAIL}}"
                
                # Format expression with values
                try:
                    sym_expr = sympy.sympify(step["expr"], evaluate=False)
                    if not step.get("result"):
                        sym_expr = sympy.Not(sym_expr)
                    subs = {}
                    for sym in sym_expr.free_symbols:
                        sym_name = str(sym)
                        if sym_name in self.params:
                            val = self.params[sym_name]
                            latex_sym = self.symbols.get(sym_name, sym_name)
                            
                            fmt = None
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

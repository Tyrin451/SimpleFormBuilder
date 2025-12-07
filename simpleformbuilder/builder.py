# Reference: e:\10_PYTHON\DEV\pysimpleform\specifications.md
# This implementation strictly follows the specifications defined in the file above.

import pint
import sympy
import numpy as np
from typing import Any, Optional, List, Dict
from .utils import security_check

ALLOWED_LOCALS = {
                "sqrt": sympy.sqrt,
                "sin": sympy.sin,
                "cos": sympy.cos,
                "tan": sympy.tan,
                "log": sympy.log,
                "exp": sympy.exp,
                "abs": sympy.Abs,
                "min": sympy.Min,
                "max": sympy.Max,
                "pi": sympy.pi,
                "all": sympy.Function("all"),
                "any": sympy.Function("any"),
            }

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
        # Sécurité et Robustesse : Validation des noms
        if not name.isidentifier():
            raise ValueError(f"Parameter name '{name}' must be a valid Python identifier.")
        
        # Sécurité et Robustesse : Gestion des types
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
        try:
            security_check(name, expr)
        except ValueError as e:
            raise ValueError(f"Equation '{name}' is invalid: {e}")

        self.symbols[name] = symbol
        
        compiled_func, args_names = self._compile_equation(name, expr)

        self.steps.append({
            "type": "eq",
            "name": name,
            "symbol": symbol,
            "expr": expr,
            "unit": unit,
            "desc": desc,
            "hidden": hidden,
            "fmt": fmt,
            "compiled_func": compiled_func,
            "args_names": args_names
        })

    def add_check(self, expr: str, desc: str, name: str = "Check", fmt: str = None):
        """
        Adds a validation step.
        """
        try:
            security_check(name, expr)
        except ValueError as e:
            raise ValueError(f"Check '{name}' is invalid: {e}")

        compiled_func, args_names = self._compile_equation(name, expr)

        self.steps.append({
            "type": "check",
            "name": name,
            "expr": expr,
            "desc": desc,
            "fmt": fmt,
            "compiled_func": compiled_func,
            "args_names": args_names
        })

    def evaluate(self):
        """
        Executes all registered calculations sequentially.
        """
        # 3.2.4 evaluate - Contexte d'évaluation
        import math
        
        # Helper to resolve arguments
        def get_arg_value(arg_name):
            if arg_name.startswith("UNIT_"):
                unit_name = arg_name[5:]
                # Resolve unit
                if hasattr(self.ureg, unit_name):
                    return getattr(self.ureg, unit_name)
                elif unit_name in self.ureg:
                    return self.ureg[unit_name]
                else:
                    raise ValueError(f"Unknown unit '{unit_name}' needed for calculation.")
            elif arg_name in self.params:
                return self.params[arg_name]
            else:
                 raise KeyError(f"Variable '{arg_name}' not found.")

        for step in self.steps:
            if step["type"] == "eq":
                try:
                    compiled_func = step["compiled_func"]
                    args_names = step["args_names"]
                    
                    args = [get_arg_value(arg) for arg in args_names]
                    
                    # 3.2.4 evaluate - 2. Evaluer
                    result = compiled_func(*args)
                    
                    # 3.2.4 evaluate - 4. Conversion d'unité
                    if step["unit"]:
                        if isinstance(result, pint.Quantity):
                            result = result.to(step["unit"])
                        else:
                             result = self.ureg.Quantity(result, step["unit"])

                    # 3.2.4 evaluate - 5. Stocker le résultat
                    self.params[step["name"]] = result
                    step["result"] = result
                    
                except ZeroDivisionError:
                    raise ZeroDivisionError(f"Division by zero in equation '{step['name']}': {step['expr']}")
                except pint.DimensionalityError as e:
                    raise pint.DimensionalityError(e.units1, e.units2, e.extra_msg) from e
                except Exception as e:
                    raise RuntimeError(f"Error evaluating equation '{step['name']}': {e}")

            elif step["type"] == "check":
                try:
                    compiled_func = step["compiled_func"]
                    args_names = step["args_names"]
                    
                    args = [get_arg_value(arg) for arg in args_names]
                    
                    # 3.2.4 evaluate - 2. Evaluer expr (booléen)
                    result = compiled_func(*args)
                    
                    # Handle numpy array results
                    if isinstance(result, np.ndarray):
                        step["result"] = bool(result.all())
                    else:
                        step["result"] = bool(result)
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
            
        # 1. Resolve dependencies recursively
        # Build a map of all equation expressions
        eq_map = {s["name"]: s["expr"] for s in self.steps if s["type"] == "eq"}
        
        import sympy
        # Use simple symbol extraction first
        local_dict = {k: sympy.Symbol(k) for k in self.params.keys()}
        
        def parse_expr(e_str):
            try:
                return sympy.sympify(e_str, locals=local_dict)
            except:
                return sympy.sympify(e_str)

        sym_expr = parse_expr(eq_step["expr"])
        
        sim_expr = parse_expr(eq_step["expr"])
        
        # We do NOT substitute equations recursively anymore.
        # This allows the user to override intermediate variables in the DataFrame.
        # If an intermediate variable is missing from DF, it will be fetched from self.params.
        # This satisfies test_lambdify_dependency_chain.
        
        sym_expr = sim_expr

        free_symbols = list(sym_expr.free_symbols)
        free_symbol_names = [str(s) for s in free_symbols]
        
        # Create lambdified function
        # Use numpy backend. Pint usually interoperates well with numpy functions (sin/cos)
        f = sympy.lambdify(free_symbols, sym_expr, modules=["numpy", "math"])
        
        target_unit = eq_step.get("unit")

        def wrapper(df):
            # df can be DataFrame or dict-like
            args = []
            for name in free_symbol_names:
                if name in df:
                    # Input from DataFrame/Dict
                    val = df[name]
                    
                    # Convert to numpy/values if possible to avoid Series index alignment issues
                    if hasattr(val, "values"):
                        val = val.values
                    elif isinstance(val, (list, tuple)):
                        val = np.array(val)
                    
                    # 2. Inject Units if applicable
                    # If the parameter exists in self.params and has a unit, apply it
                    # We assume the input in 'df' is the Magnitude of that unit.
                    if name in self.params:
                        default_val = self.params[name]
                        if isinstance(default_val, pint.Quantity):
                            # Multiply by units. 
                            # If val is numpy array, result is Quantity array (object)
                            val = val * default_val.units
                            
                    args.append(val)
                elif name in self.params:
                    # Constant from params
                    args.append(self.params[name])
                else:
                    raise KeyError(f"Variable '{name}' required for equation '{name}' (resolved) not found in DataFrame or Builder parameters.")
            
            # Calculate
            res = f(*args)
            
            # 3. Convert to target unit
            if target_unit:
                if isinstance(res, pint.Quantity):
                    res = res.to(target_unit)
                # If res is not a Quantity (e.g. unitless calculation), we might not want to force it
                # unless we are sure. But 'add_equation' with unit implies expectation.
                
            return res
        
        return wrapper

    def __getitem__(self, key: str) -> Any:
        """
        Allows dictionary-style access to parameters and results.
        """
        return self.params[key]

    def report(self, row_templates: Optional[Dict[str, str]] = None, environment: str = "align*") -> str:
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

        lines = [f"\\begin{{{environment}}}"]

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

        lines.append(f"\\end{{{environment}}}")
        return "\n".join(lines)

    def _compile_equation(self, name: str, expr: str):
        """
        Compiles an equation expression using SymPy and lambdify.
        Returns the compiled function and argument names.
        """
        try:
            # Définir le contexte autorisé pour le parsing
            allowed_locals = ALLOWED_LOCALS.copy()

            valid_symbols = set(self.params.keys())
            for step_item in self.steps:
                if step_item.get("name"):
                    valid_symbols.add(step_item["name"])

            # Gestion des unités (u.meter -> UNIT_meter)
            import re

            def unit_replacer(match):
                unit_name = match.group(1)
                # Vérifier si l'unité existe dans pint
                if not hasattr(self.ureg, unit_name):
                    # On pourrait valider plus strictement ici
                    pass
                return f"UNIT_{unit_name}"

            expr_processed = re.sub(r"\bu\.([a-zA-Z_]\w*)", unit_replacer, expr)

            used_units = re.findall(r"UNIT_([a-zA-Z_]\w*)", expr_processed)
            for u_name in used_units:
                sym_name = f"UNIT_{u_name}"
                allowed_locals[sym_name] = sympy.Symbol(sym_name)

            for sym_name in valid_symbols:
                allowed_locals[sym_name] = sympy.Symbol(sym_name)

            # Parsing sécurisé
            sym_expr = sympy.sympify(expr_processed, locals=allowed_locals)

            # Validation stricte : vérifier que tous les symboles libres sont connus
            # RELAXED: On autorise les symboles inconnus pour permettre lambdify (inputs externes)
            # for sym in sym_expr.free_symbols:
            #    s_name = str(sym)
            #    if s_name not in allowed_locals:
            #         raise ValueError(f"Unknown symbol '{sym}' in expression '{expr}'.")

            # Compilation avec lambdify
            args_syms = sorted(list(sym_expr.free_symbols), key=lambda s: str(s))
            args_names = [str(s) for s in args_syms]

            compiled_func = sympy.lambdify(args_syms, sym_expr, modules=["numpy", "math"])
            return compiled_func, args_names

        except Exception as e:
            raise ValueError(f"Invalid or unsafe expression '{expr}' for '{name}': {e}")
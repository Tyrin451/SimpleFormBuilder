import pint
import sympy
import numpy as np
import re
import math
from typing import Any, Optional, List, Dict
from .utils import security_check
from .templates import LaTeXTemplateLibrary

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

class CalculationGraph:
    """
    Manages the structure of parameters, equations, and checks.
    """
    def __init__(self):
        self.params: Dict[str, Any] = {}
        self.symbols: Dict[str, str] = {}
        self.steps: List[Dict[str, Any]] = []

    def _validate_expression(self, name: str, expr: str):
        """
        Validates the mathematical expression for security and correctness.

        Args:
            name (str): The name associated with the expression.
            expr (str): The mathematical expression to validate.

        Raises:
            ValueError: If the name is invalid, the expression contains forbidden patterns,
                or uses undefined variables/functions.
        """
        # Validate name
        if not name.isidentifier():
             raise ValueError(f"Name '{name}' must be a valid Python identifier.")

        # Security check
        try:
            security_check(name, expr)
        except ValueError as e:
            raise ValueError(f"Invalid expression for '{name}': {e}")
        
        # Note: Further AST/Symbolic validation could be added here if needed,
        # checking against self.params and self.symbols.


    def add_param(self, name: str, symbol: str, value: Any, desc: str = "", hidden: bool = False, fmt: str = None):
        """
        Registers a constant parameter in the calculation graph.

        Args:
            name (str): Unique identifier for the parameter (must be a valid Python identifier).
            symbol (str): LaTeX representation of the parameter symbol (e.g., "\\sigma").
            value (int, float, pint.Quantity, np.ndarray): The numerical value or physical quantity.
            desc (str, optional): A description of the parameter. Defaults to "".
            hidden (bool, optional): If True, the parameter will not appear in the generated report. Defaults to False.
            fmt (str, optional): Format string for displaying the value (e.g., ".2f"). Defaults to None.

        Raises:
            ValueError: If `name` is not a valid Python identifier.
            TypeError: If `value` is not one of the accepted types (int, float, pint.Quantity, np.ndarray).
        """
        # Name validation
        if not name.isidentifier():
            raise ValueError(f"Parameter name '{name}' must be a valid Python identifier.")
        
        # Type validation
        if not isinstance(value, (int, float, pint.Quantity, np.ndarray)):
             raise TypeError(f"Value for '{name}' must be an int, float, pint.Quantity, or np.ndarray. Got {type(value)}.")

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

        Args:
            name (str): Unique identifier for the result variable.
            symbol (str): LaTeX representation of the result symbol.
            expr (str): The mathematical expression as a string.
            unit (Any, optional): The expected unit of the result. If provided, the result will be converted to this unit. Defaults to None.
            desc (str, optional): Description of the equation. Defaults to "".
            hidden (bool, optional): If True, this step will be hidden in the report. Defaults to False.
            fmt (str, optional): Format string for the result. Defaults to None.

        Raises:
            ValueError: If `name` is invalid or `expr` contains forbidden content.
        """
        # Validation
        self._validate_expression(name, expr)

        self.symbols[name] = symbol
        
        # Validation of cycles could be done here (optional placeholder)
        # Note: cycles are not checked for now assumed to be handled by the user
        # self.validate_graph(current_node=name, dependencies=self._extract_deps(expr))

        self.steps.append({
            "type": "eq",
            "name": name,
            "symbol": symbol,
            "expr": expr,
            "unit": unit,
            "desc": desc,
            "hidden": hidden,
            "fmt": fmt,
            "compiled_func": None, # Delayed compilation
            "args_names": []
        })

    def add_check(self, expr: str, desc: str, name: str = "Check", fmt: str = None):
        """
        Registers a check/validation step (boolean expression).

        Args:
            expr (str): The boolean expression to evaluate (e.g. "x > 0").
            desc (str): Description of what is being checked.
            name (str, optional): Identifier for the check. Defaults to "Check".
            fmt (str, optional): Format string for values displayed in the check expression. Defaults to None.

        Raises:
            ValueError: If `expr` is invalid or unsafe.
        """
        # Validation
        self._validate_expression(name, expr)

        # Validation of cycles (optional placeholder)
        # self.validate_graph(current_node=name, dependencies=self._extract_deps(expr))

        self.steps.append({
            "type": "check",
            "name": name,
            "expr": expr,
            "desc": desc,
            "fmt": fmt,
            "compiled_func": None, # Delayed compilation
            "args_names": []
        })

    # def validate_graph(self, current_node: str, dependencies: List[str]):
    #     """
    #     Validates the absence of cycles in the calculation graph.
    #     Currently a placeholder.
    #     """
    #     # TODO: Implement cycle detection logic
    #     pass

    # def _extract_deps(self, expr: str) -> List[str]:
    #      # Rough extraction for placeholder validation
    #      # This is not perfect but serves the placeholder purpose
    #      return re.findall(r'\b[a-zA-Z_]\w*\b', expr)


class CalculationEngine:
    """
    Handles calculation execution and evaluation.
    """
    def __init__(self, ureg: Optional[pint.UnitRegistry] = None):
        self.ureg = ureg if ureg else pint.UnitRegistry()

    def _evaluate_raw_expression(self, step: Dict[str, Any], graph: CalculationGraph, get_arg_value) -> Any:
        """
        Helper to compile (if needed) and evaluate a step's expression.
        """
        if step["compiled_func"] is None:
                compiled_func, args_names = self._compile_equation(step["name"], step["expr"], graph)
                step["compiled_func"] = compiled_func
                step["args_names"] = args_names

        compiled_func = step["compiled_func"]
        args_names = step["args_names"]
        
        args = [get_arg_value(arg) for arg in args_names]
        
        return compiled_func(*args)

    def evaluate(self, graph: CalculationGraph):
        """
        Executes all registered calculations sequentially.
        """

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
            elif arg_name in graph.params:
                return graph.params[arg_name]
            else:
                 raise KeyError(f"Variable '{arg_name}' not found.")

        for step in graph.steps:
            if step["type"] == "eq":
                try:
                    # evaluation
                    result = self._evaluate_raw_expression(step, graph, get_arg_value)
                    
                    # conversion d'unité
                    if step["unit"]:
                        if isinstance(result, pint.Quantity):
                            result = result.to(step["unit"])
                        else:
                             result = self.ureg.Quantity(result, step["unit"])

                    # stockage
                    graph.params[step["name"]] = result
                    step["result"] = result
                    
                except ZeroDivisionError:
                    raise ZeroDivisionError(f"Division by zero in equation '{step['name']}': {step['expr']}")
                except pint.DimensionalityError as e:
                    raise pint.DimensionalityError(e.units1, e.units2, e.extra_msg) from e
                except Exception as e:
                    raise RuntimeError(f"Error evaluating equation '{step['name']}': {e}")

            elif step["type"] == "check":
                try:
                    # evaluation (booléen)
                    result = self._evaluate_raw_expression(step, graph, get_arg_value)
                    
                    # Handle numpy array results
                    if isinstance(result, np.ndarray):
                        step["result"] = bool(result.all())
                    else:
                        step["result"] = bool(result)
                except Exception as e:
                     raise RuntimeError(f"Error evaluating check '{step['desc']}': {e}")
                     

    def lambdify_equation(self, graph: CalculationGraph, name: str) -> Any:
        """
        Creates a function from the specified equation compatible with pandas.DataFrame.assign.

        Mechanisms:
        1. **Variable Resolution Priority**:
           - **DataFrame/Input Dict**: Variables present in the input `df` (columns or keys) are used first.
           - **Parameters**: If a variable is not in `df` but exists in `SimpleFormBuilder.params`, it is treated as a constant.
           - **Error**: If missing in both, a `KeyError` is raised.

        2. **Unit Injection**:
           - If a variable comes from `df` but also exists in `params` as a `pint.Quantity`, the corresponding unit is automatically injected (multiplied) into the values from `df`. This ensures unit consistency within the expression.

        3. **Unit Output**:
           - If the equation has a target `unit` defined, the result is converted to that unit before being returned.
        
        4. **Chained Evaluation**:
           - Dependencies that are also equations in the graph are recursively expanded.
           - This ensures the generated function depends only on base parameters/inputs, not intermediate calculation results from the builder's state.

        Args:
            graph (CalculationGraph): The calculation graph containing equations and parameters.
            name (str): The name of the equation to lambdify.

        Returns:
            Callable[[DataFrame | dict], Series | np.ndarray]: A function that accepts a DataFrame or dict and returns the calculated result.
        
        Raises:
            KeyError: If the equation is not found.
        """
        # Find the equation step
        eq_step = None
        for step in graph.steps:
            if step.get("type") == "eq" and step.get("name") == name:
                eq_step = step
                break
        
        if not eq_step:
            raise KeyError(f"Equation '{name}' not found.")
        
        # Reuse internal compilation logic with expansion for chained eval
        compiled_func, args_names = self._compile_equation(name, eq_step["expr"], graph, expand=True)
        
        target_unit = eq_step.get("unit")

        def wrapper(df):
            # df can be DataFrame or dict-like
            args = []
            for arg_name in args_names:
                # 1. Handle unit constants injected by _compile_equation (e.g. UNIT_meter)
                if arg_name.startswith("UNIT_"):
                    unit_name = arg_name[5:]
                    if hasattr(self.ureg, unit_name):
                        val = getattr(self.ureg, unit_name)
                    elif unit_name in self.ureg:
                         val = self.ureg[unit_name]
                    else:
                         raise ValueError(f"Unknown unit '{unit_name}' in equation.")
                    args.append(val)
                    continue

                # 2. Handle DataFrame/Dict input
                if arg_name in df:
                    val = df[arg_name]
                    
                    # Convert to numpy/values if possible
                    if hasattr(val, "values"):
                        val = val.values
                    elif isinstance(val, (list, tuple)):
                        val = np.array(val)
                    
                    # 3. Inject Units from params if applicable
                    # If the variable exists in params with a unit, we multiply the raw dataframe values by that unit.
                    if arg_name in graph.params:
                        default_val = graph.params[arg_name]
                        if isinstance(default_val, pint.Quantity):
                             # Only apply unit if val is NOT already a Quantity
                             if not isinstance(val, pint.Quantity):
                                val = val * default_val.units
                            
                    args.append(val)
                
                # 4. Handle constant from params
                elif arg_name in graph.params:
                    args.append(graph.params[arg_name])
                
                else:
                    raise KeyError(f"Variable '{arg_name}' required for equation '{name}' not found in DataFrame or Builder parameters.")
            
            # Calculate
            res = compiled_func(*args)
            
            # 5. Convert to target unit
            if target_unit:
                if isinstance(res, pint.Quantity):
                    res = res.to(target_unit)
                # Note: if res is not a Quantity (concerns about unit validation failure?), we might skip.
                # But typically it should be if inputs had units.
            else:
                if res.dimensionless:
                    res = res.magnitude
                
            return res
        
        return wrapper

    def _compile_equation(self, name: str, expr: str, graph: CalculationGraph, expand: bool = False):
        """
        Compiles an equation expression using SymPy and lambdify.
        
        Args:
            name: Equation name.
            expr: Mathematical expression string.
            graph: CalculationGraph instance.
            expand: If True, recursively substitutes dependencies that are other equations.
        """
        try:
            # Définir le contexte autorisé pour le parsing
            allowed_locals = ALLOWED_LOCALS.copy()

            valid_symbols = set(graph.params.keys())
            for step_item in graph.steps:
                if step_item.get("name"):
                    valid_symbols.add(step_item["name"])

            # Helper for unit replacement (u.meter -> UNIT_meter)
            def process_expression_string(raw_expr):
                def unit_replacer(match):
                    unit_name = match.group(1)
                    # We could check existence, but simpler to just map
                    return f"UNIT_{unit_name}"
                
                proc_expr = re.sub(r"\bu\.([a-zA-Z_]\w*)", unit_replacer, raw_expr)
                
                # Update allowed_locals with found units
                used_units = re.findall(r"UNIT_([a-zA-Z_]\w*)", proc_expr)
                for u_name in used_units:
                    sym_name = f"UNIT_{u_name}"
                    if sym_name not in allowed_locals:
                        allowed_locals[sym_name] = sympy.Symbol(sym_name)
                
                return proc_expr

            expr_processed = process_expression_string(expr)

            for sym_name in valid_symbols:
                allowed_locals[sym_name] = sympy.Symbol(sym_name)

            # Parsing sécurisé de l'expression initiale
            sym_expr = sympy.sympify(expr_processed, locals=allowed_locals)
            
            if expand:
                # Recursive substitution of intermediate equations
                max_depth = 20
                current_depth = 0
                
                while current_depth < max_depth:
                    free_syms = sym_expr.free_symbols
                    subs_dict = {}
                    performed_sub = False
                    
                    for sym in free_syms:
                        sym_str = str(sym)
                        # Check if this symbol matches an existing Equation in the graph
                        # We should skip if it's a Parameter (leaf)
                        step = next((s for s in graph.steps if s.get("name") == sym_str), None)
                        
                        if step and step["type"] == "eq":
                            # Found an intermediate equation defined in the graph
                            sub_expr_str = step["expr"]
                            
                            # Process units in the sub-expression
                            sub_expr_processed = process_expression_string(sub_expr_str)
                            
                            # Sympify
                            sub_sym_expr = sympy.sympify(sub_expr_processed, locals=allowed_locals)
                            
                            subs_dict[sym] = sub_sym_expr
                            performed_sub = True
                    
                    if not performed_sub:
                        break
                        
                    sym_expr = sym_expr.subs(subs_dict)
                    current_depth += 1
                
                if current_depth == max_depth:
                     raise RecursionError(f"Max recursion depth reached while expanding equation '{name}'. Possible cycle.")

            # Compilation avec lambdify
            args_syms = sorted(list(sym_expr.free_symbols), key=lambda s: str(s))
            args_names = [str(s) for s in args_syms]

            compiled_func = sympy.lambdify(args_syms, sym_expr, modules=["numpy", "math"])
            return compiled_func, args_names

        except Exception as e:
            raise ValueError(f"Invalid or unsafe expression '{expr}' for '{name}': {e}")


class LaTeXFormatter:
    """
    Dedicated format and generation of the LaTeX report.
    """
    def __init__(self, precision: int = 2, template: Any = "standard"):
        self.precision = precision
        self.template = LaTeXTemplateLibrary.get_template(template)

    def _format_value(self, val: Any, fmt_spec: Optional[str] = None) -> str:
        """Helper to format a value using the specified precision/format."""
        if fmt_spec:
            f_str = f"{{:{fmt_spec}}}"
        else:
            f_str = f"{{:.{self.precision}f}}"

        if isinstance(val, pint.Quantity):
            mag = val.magnitude
            if isinstance(mag, np.ndarray):
                # Array formatting
                mag_str = r'\begin{bmatrix}' + np.array2string(
                    mag, 
                    precision=self.precision, 
                    separator=r'\\', 
                    formatter={'float_kind' : lambda x : f_str.format(x)}
                ).strip("[]") + r'\end{bmatrix}'
            else:
                # Scalar formatting
                mag_str = f_str.format(mag)
            
            unit_str = rf"\ {val.units:~L}"
            return f"{mag_str}{unit_str}".replace("%", r"\%")
            
        elif isinstance(val, (int, float)):
            return f_str.format(val).replace("%", r"\%")
            
        elif isinstance(val, np.ndarray):
            return np.array2string(
                val, 
                precision=self.precision, 
                separator=', ', 
                formatter={'float_kind' : lambda x : f_str.format(x)}
            )
        else:
            return str(val)

    def _format_expr(self, expr_str: str, graph: CalculationGraph) -> str:
        """Helper to format an expression string to LaTeX."""
        try:
            local_dict = {name: sympy.Symbol(name) for name in graph.params.keys()}
            sym_expr = sympy.sympify(expr_str, locals=local_dict, evaluate=False)
            symbol_names = {sympy.Symbol(name): sym for name, sym in graph.symbols.items()}
            return sympy.latex(sym_expr, symbol_names=symbol_names)
        except Exception:
            return expr_str.replace("**", "^").replace("*", r"\cdot ")

    def report(self, graph: CalculationGraph, row_templates: Optional[Dict[str, str]] = None, environment: Optional[str] = None) -> str:
        """
        Generates the LaTeX report.
        
        Args:
            graph: The calculation graph.
            row_templates: Optional overrides for specific row types.
            environment: Optional override for the environment. If provided (not None), it overrides the template's environment settings for ALL steps.
        """
        # 1. Resolve effective template configuration
        current_template = self.template.copy()
        
        # Merge row_templates if provided
        if row_templates:
            current_template["rows"] = current_template.get("rows", {}).copy()
            current_template["rows"].update(row_templates)
            
        rows_config = current_template.get("rows", {})
        envs_config = current_template.get("environments", {})

        lines = []
        current_env = None

        for step in graph.steps:
            if step.get("hidden", False):
                continue
            
            step_type = step["type"]
            
            # Determine required environment
            # Priority: 
            # 1. `environment` argument (if explicit override provided)
            # 2. Template `environments` config for this type
            # 3. Default "align*"
            
            if environment is not None:
                req_env = environment
            else:
                req_env = envs_config.get(step_type, "align*")
            
            # Environment switching
            if current_env != req_env:
                if current_env is not None:
                    lines.append(f"\\end{{{current_env}}}")
                
                if req_env is not None:
                    lines.append(f"\\begin{{{req_env}}}")
                
                current_env = req_env

            # Prepare data for template
            data = {
                "symbol": step.get("symbol", ""),
                "name": step.get("name", ""),
                "desc": step.get("desc", ""),
                "value": "",
                "expr": "",
                "status": ""
            }

            if step_type == "param":
                data["value"] = self._format_value(step["value"], step.get("fmt"))
                
            elif step_type == "eq":
                data["value"] = self._format_value(step.get("result"), step.get("fmt"))
                data["expr"] = self._format_expr(step["expr"], graph)
                
            elif step_type == "check":
                data["status"] = r"\textbf{\textcolor{green}{OK}}" if step.get("result") else r"\textbf{\textcolor{red}{NOK}}"
                try:
                    local_dict = {name: sympy.Symbol(name) for name in graph.params.keys()}
                    sym_expr = sympy.sympify(step["expr"], locals=local_dict, evaluate=False)
                    if not step.get("result"):
                        sym_expr = sympy.Not(sym_expr)
                    subs = {}
                    for sym in sym_expr.free_symbols:
                        sym_name = str(sym)
                        if sym_name in graph.params:
                            val = graph.params[sym_name]
                            latex_sym = graph.symbols.get(sym_name, sym_name)
                            fmt = step.get("fmt")
                            if fmt is None:
                                for s in graph.steps:
                                    if s.get("name") == sym_name:
                                        fmt = s.get("fmt")
                                        break
                            val_str = self._format_value(val, fmt)
                            # Simple substitution for logic display
                            new_sym_latex = rf"{{{latex_sym}}} = {val_str}"
                            subs[sym] = sympy.Symbol(new_sym_latex)
                    data["expr"] = sympy.latex(sym_expr.subs(subs))
                except Exception:
                    data["expr"] = self._format_expr(step["expr"], graph)

            # Render row
            try:
                row_tpl = rows_config.get(step_type, "")
                line = row_tpl.format(**data)
                lines.append(line)
            except Exception as e:
                lines.append(f"% Error rendering step {step.get('name')}: {e}")

        # Close final environment
        if current_env is not None:
            lines.append(f"\\end{{{current_env}}}")

        return "\n".join(lines)


class SimpleFormBuilder:
    """
    Facade for creating physical calculation reports, orchestrating Graph, Engine and Formatter.
    """

    def __init__(self, precision: int = 2, template: str = "standard"):
        """
        Initializes the builder composition.

        Attributes:
            graph (CalculationGraph): Stores logic.
            engine (CalculationEngine): Executes logic.
            formatter (LaTeXFormatter): Formats output.
        """
        self.graph = CalculationGraph()
        self.engine = CalculationEngine()
        self.formatter = LaTeXFormatter(precision=precision, template=template)

    @property
    def ureg(self):
        return self.engine.ureg

    @property
    def params(self):
        return self.graph.params

    @property
    def symbols(self):
        return self.graph.symbols
    
    @property
    def steps(self):
        return self.graph.steps
    
    @property
    def precision(self):
        return self.formatter.precision
    
    @precision.setter
    def precision(self, value):
        self.formatter.precision = value

    def add_param(self, name: str, symbol: str, value: Any, desc: str = "", hidden: bool = False, fmt: str = None):
        """
        Registers a constant parameter.

        Args:
            name (str): Unique identifier for the parameter (valid Python identifier).
            symbol (str): LaTeX representation (e.g., "\\sigma").
            value (int, float, pint.Quantity, np.ndarray): Numerical value or Quantity.
            desc (str, optional): Description. Defaults to "".
            hidden (bool, optional): Hide from report. Defaults to False.
            fmt (str, optional): Format string. Defaults to None.
        """
        self.graph.add_param(name, symbol, value, desc, hidden, fmt)

    def add_equation(self, name: str, symbol: str, expr: str, unit: Any = None, desc: str = "", hidden: bool = False, fmt: str = None):
        """
        Registers an equation to be calculated.

        Args:
            name (str): Unique identifier for the result.
            symbol (str): LaTeX representation.
            expr (str): Mathematical expression.
            unit (Any, optional): Expected unit. Defaults to None.
            desc (str, optional): Description. Defaults to "".
            hidden (bool, optional): Hide from report. Defaults to False.
            fmt (str, optional): Format string. Defaults to None.
        """
        self.graph.add_equation(name, symbol, expr, unit, desc, hidden, fmt)
        # Compatibility: Pre-compilation check could happen here if we wanted to enforce fail-fast nature of original code.
        # But we delegate actual compilation to evaluate() or explicit lambdify.
        # To strictly better separate concerns, validation is done in Graph (security), logic in Engine.

    def add_check(self, expr: str, desc: str, name: str = "Check", fmt: str = None):
        """
        Adds a validation step.

        Args:
            expr (str): Boolean expression.
            desc (str): Description.
            name (str, optional): Identifier. Defaults to "Check".
            fmt (str, optional): Format string. Defaults to None.
        """
        self.graph.add_check(expr, desc, name, fmt)

    def evaluate(self):
        """
        Executes all registered calculations sequentially.
        """
        self.engine.evaluate(self.graph)

    def lambdify_equation(self, name: str) -> Any:
        """
        Creates a function from the specified equation compatible with pandas.DataFrame.assign.

        Mechanisms:
        1. **Variable Resolution Priority**:
           - **DataFrame/Input Dict**: Variables present in the input `df` (columns or keys) are used first.
           - **Parameters**: If a variable is not in `df` but exists in `SimpleFormBuilder.params`, it is treated as a constant.
           - **Error**: If missing in both, a `KeyError` is raised.

        2. **Unit Injection**:
           - If a variable comes from `df` but also exists in `params` as a `pint.Quantity`, the corresponding unit is automatically injected (multiplied) into the values from `df`. This ensures unit consistency within the expression.

        3. **Unit Output**:
           - If the equation has a target `unit` defined, the result is converted to that unit before being returned.

        Args:
            name (str): The name of the equation.

        Returns:
            Callable: compiled function.
        """
        return self.engine.lambdify_equation(self.graph, name)

    def __getitem__(self, key: str) -> Any:
        """
        Allows dictionary-style access to parameters and results.
        """
        return self.graph.params[key]

    def report(self, row_templates: Optional[Dict[str, str]] = None, environment: str = None) -> str:
        """
        Generates the LaTeX report.

        Args:
            row_templates (Dict[str, str], optional): Custom templates.
            environment (str, optional): LaTeX environment override. 
                                         If None (default), uses the template's defined environments.
                                         If provided, forces all steps to this environment.

        Returns:
            str: The generated LaTeX code.
        """
        return self.formatter.report(self.graph, row_templates, environment)
---
name: SimpleFormBuilder
description: Use this skill whenever the user wants to create a technical calculation note, engineering formula sheet, or physics verification report in Python.
---

## Setup the import

```python
from simpleformbuilder.builder import SimpleFormBuilder

builder = SimpleFormBuilder()  # base object
u = builder.ureg  # Pint register — always use u.xxx for the units.
```

## API Reference

### `add_param(name, symbol, value, desc="", hidden=False, fmt=None)`

Add a parameter of the calculation.

- `name` : valid python variable/identifier (ex: `sigma_adm`)
- `symbol` : raw Latex string (ex: `r"\sigma_{adm}"`)
- `value` : scalar or value with Pint unit (ex: `100 * u.MPa`)
- `hidden` : if true, this parameter is hidden in report
- `fmt` : numeric format of the parameter (ex: `".2f"`, `".0f"`)

```python
builder.add_param("Fx", r"F_x", 10 * u.kN, desc="Force axiale")
builder.add_param("A",  r"A",   50 * u.cm**2, desc="Section transversale")
builder.add_param("sigma_adm", r"\sigma_{adm}", 100 * u.MPa, desc="Contrainte admissible")
```

### `add_equation(name, symbol, expr, unit=None, desc="", hidden=False, fmt=None)`

Defined a new value computed from symbolic expression.

- `expr` : mathematical expression with parameter and operator (ex: `"Fx / A"`)
- `unit` : Pint target unit unité cible Pint for the automatic conversion of the result
- The dependencies are resolved in their adding order.

```python
builder.add_equation("sigma", r"\sigma", "Fx / A", unit=u.MPa, desc="Contrainte calculée")
```
**Supported operator :** `+`, `-`, `*`, `/`, `**`, `sqrt`, `sin`, `cos`, `abs`  
**To avoid :** specific python syntaxe , `__dunder__`, ternary condition

### `add_check(expr, desc, name="Check", fmt=None)`

Add boolean verification. 

- `expr` : boolean expression (ex: `"sigma <= sigma_adm"`)

```python
builder.add_check("sigma <= sigma_adm", desc="Vérification de la contrainte")
```

**Note** : Prefere use "<=" or ">=".

### `evaluate()`

Execute all computation in added order. **Must be call before `report()`.**
If parameter are modified, recall `evaluate()`.

### `report(row_templates=None, environment=None)`

Generate the latex report.

- `environment` : force un environnement LaTeX spécifique (`"align*"`, `"gather"`, etc.)
- `row_templates` : dict optionnel pour personnaliser le rendu ligne par ligne (`"param"`, `"eq"`, `"check"`)

**Templates disponibles** (passés à `SimpleFormBuilder(template=...)`) :
- `"standard"` (défaut) : tableau avec descriptions
- `"compact"` : sans descriptions textuelles

```python
builder.evaluate()
report = builder.report()
print(report)
# ou dans Marimo/Jupyter : mo.md(report) / display(Markdown(report))
```

### `lambdify_equation(name)`

Return a vectorized function (lambdify).
Useful for `df.assign()` with the pandas library.

The variables are solved in this priority order.
2. The named parameter in dataframe column overload everything.
2. Intermediary equation in builder (chained calculation)
3. Constant parameter in the builder (default value)

```python
builder.add_param("A", r"A", 50 * u.cm**2)
builder.add_equation("sigma", r"\sigma", "Fx / A", unit=u.MPa)

calc_sigma = builder.lambdify_equation("sigma")

df = pd.DataFrame({'Fx': [10, 20, 30] * u.kN})
df = df.assign(sigma=calc_sigma)  # A est pris dans les params du builder
```

## Complete Workflow example

```python
from simpleformbuilder.builder import SimpleFormBuilder

builder = SimpleFormBuilder()
u = builder.ureg

# 1. Parameters
builder.add_param("Fx", r"F_x", 10 * u.kN, desc="Force axiale")
builder.add_param("A", r"A", 50 * u.cm**2, desc="Section transversale")
builder.add_param("sigma_adm", r"\sigma_{adm}", 100 * u.MPa, desc="Contrainte admissible")

# 2. Equation
builder.add_equation("sigma", r"\sigma", "Fx / A", unit=u.MPa, desc="Contrainte calculée")

# 3. Verification
builder.add_check("sigma <= sigma_adm", desc="Vérification de la contrainte")

# 4. Calculation / Report
builder.evaluate()
print(builder.report())
```

## Gotchas

* **Incompatible units**: Pint raises `DimensionalityError` when adding `m + kg`. Verify the dimensional consistency of expressions.
* **Evaluation order**: An equation can only reference variables defined *before* it. No circular dependencies.
* **`lambdify_equation` is used with `df.assign(col=func)**`, not `df['col'] = func(df)`.
* **LaTeX symbols**: Always use raw strings `r"\sigma"` to avoid escaping issues.
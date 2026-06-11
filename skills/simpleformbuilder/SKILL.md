---
name: SimpleFormBuilder
description: Use this skill whenever the user wants to create a technical calculation note, engineering formula sheet, or physics verification report in Python.
---

## Setup

```python
from simpleformbuilder.builder import SimpleFormBuilder

builder = SimpleFormBuilder()
u = builder.ureg  # Registre Pint — toujours utiliser u.xxx pour les unités
```

---

## API Reference

### `add_param(name, symbol, value, desc="", hidden=False, fmt=None)`

Définit une constante ou donnée d'entrée.

- `name` : identifiant Python valide (ex: `sigma_adm`)
- `symbol` : chaîne LaTeX brute (ex: `r"\sigma_{adm}"`)
- `value` : valeur avec unité Pint (ex: `100 * u.MPa`) ou scalaire pur
- `hidden` : si `True`, n'apparaît pas dans le rapport
- `fmt` : format numérique (ex: `".2f"`, `".0f"`)

```python
builder.add_param("Fx", r"F_x", 10 * u.kN, desc="Force axiale")
builder.add_param("A",  r"A",   50 * u.cm**2, desc="Section transversale")
builder.add_param("sigma_adm", r"\sigma_{adm}", 100 * u.MPa, desc="Contrainte admissible")
```

---

### `add_equation(name, symbol, expr, unit=None, desc="", hidden=False, fmt=None)`

Définit une valeur calculée par expression symbolique.

- `expr` : expression mathématique en chaîne (ex: `"Fx / A"`)
- `unit` : unité cible Pint pour la conversion automatique du résultat
- Les dépendances sont résolues automatiquement dans l'ordre d'ajout

```python
builder.add_equation("sigma", r"\sigma", "Fx / A", unit=u.MPa, desc="Contrainte calculée")
```

**Opérateurs supportés :** `+`, `-`, `*`, `/`, `**`, `sqrt`, `sin`, `cos`, `abs`  
**À éviter :** syntaxe Python spécifique, `__dunder__`, conditions ternaires

---

### `add_check(expr, desc, name="Check", fmt=None)`

Ajoute une vérification booléenne. Rendu **OK** (vert) ou **FAIL** (rouge) dans le rapport.

- `expr` : expression booléenne en chaîne (ex: `"sigma <= sigma_adm"`)

```python
builder.add_check("sigma <= sigma_adm", desc="Vérification de la contrainte")
```

---

### `evaluate()`

Exécute tous les calculs dans l'ordre d'ajout. **Doit être appelé avant `report()`.**  
Si des paramètres sont modifiés après coup, rappeler `evaluate()`.

---

### `report(row_templates=None, environment=None)`

Génère le code LaTeX du rapport.

- `environment` : force un environnement LaTeX spécifique (`"align*"`, `"gather"`, etc.)
- `row_templates` : dict optionnel pour personnaliser le rendu ligne par ligne (`"param"`, `"eq"`, `"check"`)

**Templates disponibles** (passés à `SimpleFormBuilder(template=...)`) :
- `"standard"` (défaut) : tableau avec descriptions
- `"compact"` : sans descriptions textuelles
- ~~`"detailed"`~~ : en cours de développement, ne pas utiliser

```python
builder.evaluate()
report = builder.report()
print(report)
# ou dans Marimo/Jupyter : mo.md(report) / display(Markdown(report))
```

---

### `lambdify_equation(name)`

Retourne une **fonction vectorisée** à passer à `df.assign()` pour traitement Pandas.

Résolution des variables dans cet ordre de priorité :
1. Colonnes du DataFrame (surcharge tout)
2. Équations intermédiaires du builder (calcul en chaîne)
3. Paramètres constants du builder (valeurs par défaut)

```python
builder.add_param("A", r"A", 50 * u.cm**2)
builder.add_equation("sigma", r"\sigma", "Fx / A", unit=u.MPa)

calc_sigma = builder.lambdify_equation("sigma")

df = pd.DataFrame({'Fx': [10, 20, 30] * u.kN})
df = df.assign(sigma=calc_sigma)  # A est pris dans les params du builder
```

---

## Workflow complet

```python
from simpleformbuilder.builder import SimpleFormBuilder

builder = SimpleFormBuilder()          # ou template="compact"
u = builder.ureg

# 1. Paramètres
builder.add_param("Fx", r"F_x", 10 * u.kN, desc="Force axiale")
builder.add_param("A", r"A", 50 * u.cm**2, desc="Section transversale")
builder.add_param("sigma_adm", r"\sigma_{adm}", 100 * u.MPa, desc="Contrainte admissible")

# 2. Équations
builder.add_equation("sigma", r"\sigma", "Fx / A", unit=u.MPa, desc="Contrainte calculée")

# 3. Vérifications
builder.add_check("sigma <= sigma_adm", desc="Vérification de la contrainte")

# 4. Calcul + rapport
builder.evaluate()
print(builder.report())
```

---

## Pièges fréquents

- **Unités incompatibles** : Pint lève `DimensionalityError` si on additionne `m + kg`. Vérifier la cohérence dimensionnelle des expressions.
- **Ordre d'évaluation** : une équation ne peut référencer que des variables définies *avant* elle. Pas de dépendance circulaire.
- **`lambdify_equation` s'utilise avec `df.assign(col=func)`**, pas `df['col'] = func(df)`.
- **Template `"detailed"` non disponible** : lève une erreur, utiliser `"standard"` ou `"compact"`.
- **Symboles LaTeX** : toujours utiliser des raw strings `r"\sigma"` pour éviter les problèmes d'échappement.
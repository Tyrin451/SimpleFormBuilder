# PySimpleForm

PySimpleForm est une bibliothèque Python conçue pour faciliter la création de notes de calcul techniques et physiques. Elle permet de définir des paramètres, des équations et des vérifications, puis de générer automatiquement un rapport formaté en LaTeX.

Elle s'appuie sur des bibliothèques robustes :
- **Pint** pour la gestion rigoureuse des unités physiques.
- **SymPy** pour le rendu symbolique des équations.
- **NumPy** pour les calculs numériques et vectoriels.

## Fonctionnalités

- **Définition de Paramètres** : Stockage de constantes avec leurs unités et symboles LaTeX.
- **Équations Symboliques** : Définition de formules sous forme de chaînes de caractères (ex: `"Fx / A"`), évaluées automatiquement.
- **Conversion d'Unités** : Conversion automatique des résultats dans l'unité souhaitée.
- **Vérifications (Checks)** : Tests logiques (ex: `sigma <= sigma_adm`) avec retour visuel (OK/FAIL) dans le rapport.
- **Rapport LaTeX** : Génération d'un code LaTeX prêt à l'emploi (environnement `align*`) pour une intégration facile dans des documents ou des notebooks (comme Marimo ou Jupyter).

## Installation

Le projet utilise `uv` pour la gestion des dépendances. Assurez-vous d'avoir un environnement Python (>= 3.13 recommandé) avec les dépendances suivantes :

- `pint`
- `sympy`
- `numpy`
- `marimo` (optionnel, pour l'affichage interactif)

Si vous utilisez `uv` :
```bash
uv sync
```

Ou via pip :
```bash
pip install pint sympy numpy marimo
```

## Exemple d'Utilisation

Voici comment utiliser `SimpleFormBuilder` pour créer une note de calcul simple (vérification d'une contrainte).

```python
from simpleformbuilder.builder import SimpleFormBuilder

# 1. Initialisation
builder = SimpleFormBuilder()
u = builder.ureg  # Accès au registre d'unités de Pint

# 2. Définition des paramètres
# add_param(nom_variable, symbole_latex, valeur, description)
builder.add_param("Fx", "F_x", 10 * u.kN, desc="Force axiale")
builder.add_param("A", "A", 50 * u.cm**2, desc="Section transversale")
builder.add_param("sigma_adm", r"\sigma_{adm}", 100 * u.MPa, desc="Contrainte admissible")

# 3. Définition des équations
# add_equation(nom_variable, symbole_latex, expression, unité_cible, description)
builder.add_equation(
    "sigma", 
    r"\sigma", 
    "Fx / A", 
    unit=u.MPa, 
    desc="Contrainte calculée"
)

# 4. Ajout de vérifications
# add_check(expression_logique, description)
builder.add_check("sigma <= sigma_adm", desc="Vérification de la contrainte")

# 5. Exécution des calculs
builder.evaluate()

# 6. Génération du rapport
# Le rapport est une chaîne de caractères contenant du code LaTeX
report = builder.report()

print(report)
```

### Exemple de Sortie (Rendu)

Le rapport généré ressemblera à ceci une fois rendu (par exemple dans Marimo ou LaTeX) :

$$
\begin{align*}
F_x &= 10.00\ \mathrm{kN} && \text{Force axiale} \\
A &= 50.00\ \mathrm{cm}^2 && \text{Section transversale} \\
\sigma_{adm} &= 100.00\ \mathrm{MPa} && \text{Contrainte admissible} \\
\sigma &= \frac{F_x}{A} = 2.00\ \mathrm{MPa} && \text{Contrainte calculée} \\
\text{Check} &: \sigma \leq \sigma_{adm} \rightarrow \textbf{\textcolor{green}{OK}} && \text{Vérification de la contrainte} \\
\end{align*}
$$

## Documentation de l'API

### Classe `SimpleFormBuilder`

#### `add_param(name, symbol, value, desc="", hidden=False, fmt=None)`
Enregistre un paramètre constant.
- `name` : Nom de la variable (identifiant Python valide).
- `symbol` : Symbole LaTeX pour l'affichage.
- `value` : Valeur (int, float, pint.Quantity ou np.ndarray).
- `desc` : Description textuelle.
- `fmt` : Formatage de la valeur (ex: `".2f"`, `".1%"`). Par défaut `None` (utilise la précision globale).

#### `add_equation(name, symbol, expr, unit=None, desc="", hidden=False, fmt=None)`
Enregistre une équation à calculer.
- `expr` : Expression mathématique sous forme de chaîne (ex: `"a * b + c"`).
- `unit` : Unité `pint` vers laquelle convertir le résultat.
- `fmt` : Formatage du résultat (ex: `".2f"`). Par défaut `None`.

#### `add_check(expr, desc, name="Check", fmt=None)`
Ajoute une étape de validation.
- `expr` : Expression booléenne (ex: `"x > 0"`).
- `desc` : Description de la vérification.
- `fmt` : Formatage des valeurs affichées dans l'expression (ex: `".2f"`).

#### `evaluate()`
Exécute tous les calculs et vérifications dans l'ordre où ils ont été ajoutés.

#### `report(row_templates=None)`
Génère le code LaTeX du rapport.
- `row_templates` : Dictionnaire optionnel pour personnaliser le formatage des lignes (`param`, `eq`, `check`).

#### `lambdify_equation(name)`
Génère une fonction Python exécutable à partir d'une équation enregistrée, optimisée pour `pandas`.
- `name` : Nom de l'équation à convertir.
- **Retourne** : Une fonction qui accepte un DataFrame (ou dictionnaire) et retourne le résultat calculé.
    - Utilise les colonnes du DataFrame si elles correspondent aux variables de l'équation.
    - Utilise les paramètres du `builder` pour les variables manquantes.
    - Gère automatiquement les unités `pint` et la vectorisation.

**Exemple d'utilisation avec Pandas :**
```python
# Supposons une équation "sigma" = "Fx / A" définie dans le builder
calc_sigma = builder.lambdify_equation("sigma")

# Création d'un DataFrame avec des valeurs variables pour Fx
import pandas as pd
df = pd.DataFrame({
    'Fx': [10, 20, 30] * u.kN
})

# Ajout de la colonne calculée (A est pris dans les paramètres du builder)
df = df.assign(sigma_new = calc_sigma)
```

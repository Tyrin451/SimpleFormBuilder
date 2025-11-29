# Spécifications Techniques : Générateur de Rapports de Calcul LaTeX (Python)

## 1. Vue d'ensemble
L'objectif est de développer une librairie Python autonome (sans dépendance à Jupyter Notebook) utilisant le pattern Builder. Cette librairie permet de définir séquentiellement des paramètres physiques et des équations, d'effectuer les calculs avec gestion automatique des unités, de valider des critères (checks), et de générer un rapport de calcul formaté en LaTeX.


## 2. Stack Technologique
Langage : Python 3.10 ou supérieur.
Dépendances principales :
- pint : Gestion des unités et calculs physiques.
- sympy : Parsing d'expressions et rendu LaTeX symbolique et évaluation des expressions.
- numpy (optionnel mais recommandé) : Pour les fonctions mathématiques vectorielles ou avancées si besoin, sinon le module math standard suffit.
Tests : pytest.

## 3. Architecture : Classe SimpleFormBuilder
La librairie doit exposer une classe principale SimpleFormBuilder qui orchestre le flux de travail.

### **3.1 Initialisation**

La méthode `__init__` doit configurer :

* Un **registre d'unités** (pint.UnitRegistry).  
* Une **précision globale** par défaut (ex: 2 décimales) pour l'affichage numérique.  
* Des structures de données pour stocker :  
  * Les variables (nom Python -> Objet Pint).  
  * Les symboles (nom Python -> Représentation LaTeX).  
  * La liste ordonnée des étapes (paramètres, équations, vérifications) pour la génération du rapport.

### **3.2 Méthodes de l'API**

#### `add_param`(self, name: str, symbol: str, value: Any, desc: str \= "", hidden: bool \= False, fmt: str \= None)

* **Rôle** : Enregistre une constante.  
* **Arguments** :  
  * name : Identifiant Python (ex: 'Fx'). Doit être un identifiant valide.  
  * symbol : Représentation LaTeX (ex: 'F\_x').  
  * value : Valeur numérique ou objet pint.Quantity (ex: 10 \* u.kN).  
  * desc : Description textuelle.  
  * hidden : Si True, la variable est utilisable dans les calculs mais n'apparaît pas dans le rapport LaTeX.  
  * fmt : Formatage spécifique (ex: "{:.3f}") qui surcharge la précision globale.

#### `add_equation`(self, name: str, symbol: str, expr: str, unit: Any \= None, desc: str \= "", hidden: bool \= False, fmt: str \= None)

* **Rôle** : Enregistre une formule à calculer.  
* **Arguments** :  
  * expr : Chaîne de caractères contenant la formule mathématique utilisant les noms des autres variables (ex: 'Fx / A').  
  * unit : Unité cible optionnelle. Si fournie, le résultat calculé doit être converti dans cette unité.  
  * Autres arguments identiques à add\_param.

#### `add_check`(self, expr: str, desc: str, name: str \= "Check")

* **Rôle** : Ajoute une étape de validation (critère d'ingénierie).  
* **Arguments** :  
  * expr : Une expression booléenne sous forme de chaîne (ex: 'sigma \< 200 \* u.MPa').  
  * desc : Description du critère (ex: "Vérification contrainte admissible").

#### `evaluate`(self)

* **Rôle** : Exécute séquentiellement tous les calculs enregistrés.  
* **Spécifications techniques** :  
  1. Parcourir la liste des étapes.  
  2. Pour chaque équation ou check, évaluer la chaîne expr en utilisant eval().  
  3. **Contexte d'évaluation** : Le dictionnaire passé à eval doit contenir :  
     * Toutes les variables (params) calculées précédemment.  
     * Les fonctions mathématiques standards (sqrt, sin, cos, tan, pi, log, exp) compatibles avec les unités Pint.  
  4. Gérer la conversion d'unité si le paramètre unit est présent.  
  5. Stocker le résultat.  
  6. Gestion d'erreur : Capturer et signaler clairement les divisions par zéro ou les incompatibilités d'unités.

#### `report`(self) -> str

* **Rôle** : Génère le code LaTeX du rapport.  
* **Format** : Retourne une chaîne contenant un environnement \\begin{align} ... \\end{align}.  
* **Règles de rendu** :  
  * Remplacer les opérateurs Python (\*\*, \*) par leurs équivalents LaTeX.  
  * **Substitution Symbolique** : Dans l'expression affichée, les noms de variables Python (ex: Fx) doivent être remplacés par leurs symboles LaTeX définis (ex: F\_x). Utiliser sympy pour parser et reformater l'expression proprement.  
  * **Checks** : Afficher clairement le résultat (OK/FAIL). Exemple : \\text{Check} : \\sigma \< f\_y \\implies \\text{OK}.  
  * Respecter l'argument hidden.  
  * Appliquer le formatage numérique (precision ou fmt).

## **4\. Format de Sortie LaTeX Attendu**

Le code généré doit ressembler à ceci :

\\begin{align}  
F\_x &= 10.00\\ \\text{kN} && \\text{Force axiale} \\\\  
A &= 50.00\\ \\text{cm}^2 && \\text{Section} \\\\  
\\sigma &= \\frac{F\_x}{A} \= 20.00\\ \\text{MPa} && \\text{Contrainte} \\\\  
\\text{Verif} &: \\sigma \< 235\\ \\text{MPa} \\rightarrow \\textbf{OK} && \\text{Critère Eurocode} \\\\  
\\end{align}  

## 5. Sécurité et Robustesse

* **Validation des noms** : Interdire l'utilisation de mots-clés réservés Python (ex: `def`, `class`, `lambda`) ou de noms écrasant des fonctions mathématiques (`sin`, `pi`).
* **Gestion des types** : S'assurer que les valeurs injectées dans `add_param` sont soit des nombres (`int`, `float`), soit des quantités `pint`.

## 6. Plan de Tests (`pytest`)

Les tests doivent couvrir :

1.  **Workflow Nominal** : Définition de params -> équation -> evaluate -> report. Vérifier que le LaTeX contient les bonnes valeurs.
2.  **Conversion d'unités** : Vérifier que `10 m + 50 cm` donne bien `10.5 m`.
3.  **Fonctions Mathématiques** : Tester une équation complexe incluant `sqrt` ou `sin` (ex: trigonométrie).
4.  **Checks** :
    * Cas passant (OK).
    * Cas échouant (FAIL).
5.  **Variables Cachées** : Vérifier qu'une variable `hidden=True` n'est pas dans la chaîne retournée par `report()`.
6.  **Formatage** : Vérifier le respect de la précision (ex: `.2f`).

## 7. Livrables Attendus

1.  `builder.py` : Code source de la classe.
2.  `requirements.txt` : Liste des dépendances.
3.  `main.py` : Script de démonstration simple.
4.  `tests/test_builder.py` : Fichier de tests unitaires complet.
```
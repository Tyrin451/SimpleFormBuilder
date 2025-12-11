import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from simpleformbuilder import builder
    import numpy as np
    import pandas as pd
    import pint_pandas
    return builder, mo


@app.cell
def _(builder):
    # Initialize the builder
    sf = builder.SimpleFormBuilder()

    u = sf.ureg # Accès au registre d'unités 

    # Géométrie de la soudure
    sf.add_param("a", "a", 5 * u.mm, desc="Apothème", fmt=".1f")

    # Matériau (Exemple pour S235)
    sf.add_param("Re", "R_e", 235 * u.MPa, desc="Résistance élastique")

    # Chargements (Forces extraites)
    # Fx = Cisaillement longitudinal (parallèle à l'axe)
    sf.add_param("NX", "F_{x}", 1500000 * u.N/u.m, desc="Flux Effort longitudinal")

    # Décomposition des contraintes sur le plan de gorge (à 45 degrés pour une soudure d'angle)
    sf.add_equation(
        "sig_simple", r"\sigma_{simple}", 
        "sqrt(NX**2)/a", 
        unit=u.MPa, desc="Contrainte simplifiée", fmt=".2f"
    )

    sf.add_equation(
        "sig_a", r"\sigma_{a}", 
        "Re/sqrt(2)", 
        unit=u.MPa, desc="Contrainte admissible", fmt=".2f"
    )

    sf.add_equation(
        "TC", r"TC", 
        "sig_simple/sig_a",
        desc="Taux de charge", fmt=".1f"
    )

    # --- 5. Génération ---
    sf.evaluate()
    return (sf,)


@app.cell
def _(mo, sf):
    mo.md('$$'+sf.report()+'$$')
    return


@app.cell
def _():
    dict_base2 = {"NX":1500000, "NY":5, "NZ":40, "a":5, "Re":235}
    return (dict_base2,)


@app.cell
def _(dict_base2, sf):
    sf.lambdify_equation('TC')(dict_base2)
    return


@app.cell
def _(sf):
    print(sf['TC'])
    return


@app.cell
def _(dict_base2, sf):
    print(sf.lambdify_equation('TC')(dict_base2))
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()


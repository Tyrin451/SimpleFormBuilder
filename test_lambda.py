import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from simpleformbuilder import builder
    import pandas as pd
    return builder, mo, pd


@app.cell(hide_code=True)
def _(builder, mo):
    def generer_note_kellerman(couple_serrage, d_nom, pas, mu_filet, mu_tete):
        """
        Génère une note de calcul pour l'effort de précontrainte (Kellerman-Klein).

        Args:
            couple_serrage (Quantity): Le couple appliqué (ex: 50 * u.Nm)
            d_nom (Quantity): Diamètre nominal de la vis (ex: 12 * u.mm)
            pas (Quantity): Pas du filetage (ex: 1.75 * u.mm)
            mu_filet (float): Coeff de frottement dans le filet
            mu_tete (float): Coeff de frottement sous tête
        """

        # 1. Initialisation
        sf = builder.SimpleFormBuilder() # [cite: 4]
        u = sf.ureg  # Accès au registre d'unités [cite: 10, 18]
        d_nom = d_nom * u.mm
        pas = pas * u.mm
        # --- 2. Définition des Paramètres (Entrées) --- [cite: 5]
        sf.add_param("C", "C_{serrage}", couple_serrage * u.N * u.m, desc="Couple de serrage appliqué", fmt=".1f")
        sf.add_param("d", "d", d_nom, desc="Diamètre nominal vis")
        sf.add_param("p", "p", pas, desc="Pas du filetage")

        # Coefficients de frottement
        sf.add_param("mu_th", r"\mu_{th}", mu_filet, desc="Coef. frottement filet")
        sf.add_param("mu_h", r"\mu_{h}", mu_tete, desc="Coef. frottement sous tête")

        # Géométrie standard (ISO)
        sf.add_param("alpha", r"\alpha", 60 * u.deg, desc="Angle du filet (ISO)")
        # Hypothèse : Diamètre moyen sous tête standard ~ 1.3 * d (ou à définir précisément)
        sf.add_param("D_m", "D_{m}", 1.3 * d_nom, desc="Diamètre moyen sous tête (approx)")

        # --- 3. Définition des Equations (Calculs) --- [cite: 6]

        # 3.1 Diamètre sur flanc (d2)
        # Formule approx ISO : d2 = d - 0.6495 * p
        sf.add_equation(
            "d2", 
            "d_2", 
            "d - 0.6495 * p", 
            unit=u.mm, 
            desc="Diamètre sur flanc"
        )

        # 3.2 Composantes de la formule Kellerman-Klein
        # Le couple se décompose en trois termes résistants pour trouver F0 :
        # C = F0 * (Terme_Helice + Terme_Frot_Filet + Terme_Frot_Tete)

        # a) Terme lié à la pente (hélice) : p / (2 * pi)
        sf.add_equation("K_pente", "K_{pente}", "p / (2 * pi)", unit=u.mm, desc="Facteur géométrique pente") # 

        # b) Terme lié au frottement filet : (d2 * mu_th) / (2 * cos(alpha/2))
        sf.add_equation(
            "K_filet", 
            "K_{filet}", 
            "(d2 * mu_th) / (2 * cos(alpha/2))", 
            unit=u.mm, 
            desc="Facteur frottement filet"
        )

        # c) Terme lié au frottement sous tête : (D_m * mu_h) / 2
        sf.add_equation("K_tete", "K_{tete}", "(D_m * mu_h) / 2", unit=u.mm, desc="Facteur frottement tête")

        # 3.3 Calcul Final de la Précontrainte F0
        # F0 = C / (K_pente + K_filet + K_tete)
        sf.add_equation(
            "F0", 
            "F_0", 
            "C / (K_pente + K_filet + K_tete)", 
            unit=u.N,   # Conversion automatique en kN 
            desc="Effort de précontrainte généré",
            fmt=".2f"    # Formatage 2 décimales [cite: 24]
        )

        sf.evaluate() 
        return sf 

    equations = generer_note_kellerman(
        couple_serrage=85,
        d_nom=16,
        pas=2.0,
        mu_filet=0.15,
        mu_tete=0.15
    )

    mo.md(f"$${equations.report()}$$")
    return (equations,)


@app.cell
def _(equations):
    calc_F0 = equations.lambdify_equation('F0')
    return (calc_F0,)


@app.cell
def _():
    data = {'C':[85], 'd':[16], 'p':[2], 'mu_th':[0.15], 'mu_h':[0.15]}
    return (data,)


@app.cell
def _(calc_F0, data, pd):
    df = pd.DataFrame.from_dict(data)
    df2=df.assign(F0=calc_F0)
    df2
    return


@app.cell
def _(calc_F0, data):
    result = calc_F0(data)
    result
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

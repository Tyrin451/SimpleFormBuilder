import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from simpleformbuilder import builder
    import pandas as pd
    return builder, mo, np, pd


@app.cell(hide_code=True)
def _(builder, mo):
    def _verif1():
        # 1. Initialisation
        verif = builder.SimpleFormBuilder()
        u = verif.ureg

        # 2. Définition des paramètres
        verif.add_param("Fx", "F_x", 10 * u.kN, desc="Force axiale")
        verif.add_param("A", "A", 50 * u.cm**2, desc="Section")
        verif.add_param("sigma_a", r"\sigma_a", 100 * u.MPa, desc="Contrainte admissible")

        # 3. Définition des équations
        # sigma = Fx / A
        verif.add_equation("sigma", "\\sigma", "Fx / A", unit=u.MPa, desc="Contrainte")

        # 4. Ajout de vérifications (Checks)
        verif.add_check("sigma <= sigma_a", desc="Contrainte admissible", name='Check1')
        # verif.add_check("ratio <= 1", desc="", name='Ratio', fmt='.1%')
        verif.add_equation('ratio', 'TC', 'sigma/sigma_a', desc='Taux de charge', fmt='.2%')

        # 5. Exécution des calculs
        verif.evaluate()

        # 6. Génération du rapport
        report = verif.report()
        return f'$${report}$$'

    mo.md(_verif1())
    return


@app.cell(hide_code=True)
def _(builder, mo, np):
    def _verif1():
        # 1. Initialisation
        verif = builder.SimpleFormBuilder()
        u = verif.ureg

        # 2. Définition des paramètres
        verif.add_param("Fx", "F_x", np.array([10, 20]) * u.kN, desc="Force axiale")
        verif.add_param("A", "A", 50 * u.cm**2, desc="Section")
        verif.add_param("sigma_a", r"\sigma_a", 100 * u.MPa, desc="Contrainte admissible")

        # 3. Définition des équations
        # sigma = Fx / A
        verif.add_equation("sigma", "\\sigma", "Fx / A", unit=u.MPa, desc="Contrainte")

        # 4. Ajout de vérifications (Checks)
        verif.add_check("sigma <= sigma_a", desc="Contrainte admissible", name='Check1')
        # verif.add_check("ratio <= 1", desc="", name='Ratio', fmt='.1%')
        verif.add_equation('ratio', 'TC', 'sigma/sigma_a', desc='Taux de charge', fmt='.2%')

        # 5. Exécution des calculs
        verif.evaluate()

        # 6. Génération du rapport
        report = verif.report()
        return f'$${report}$$'

    mo.md(_verif1())
    return


@app.cell(hide_code=True)
def _(builder, mo):
    def verifier_arrachement_filet():
        """
        Génère une note de calcul pour la vérification au cisaillement
        des filets (arrachement) sous charge axiale.
        """

        # 1. Initialisation
        # Création de l'instance principale et accès au registre d'unités [cite: 4, 10]
        sf = builder.SimpleFormBuilder()
        u = sf.ureg 

        # 2. Définition des Paramètres (Entrées)
        # Nous définissons la géométrie, le matériau et la charge [cite: 5]
        sf.add_param("F_t", "F_{t,Ed}", 45 * u.kN, desc="Effort de traction appliqué")
        sf.add_param("d", "d", 16 * u.mm, desc="Diamètre nominal du filet")
        sf.add_param("L_e", "L_{eng}", 12 * u.mm, desc="Longueur en prise")
        sf.add_param("Re", "R_{e}", 235 * u.MPa, desc="Limite élastique du matériau")
        sf.add_param("gamma_M", r"\gamma_M", 1.25, desc="Coefficient de sécurité")

        # Facteur de forme pour la surface de cisaillement (souvent ~0.6 pour filetage ISO)
        sf.add_param("k_cis", "k_{cis}", 0.6, desc="Facteur de section cisaillée")

        # 3. Définition des Équations
        # Calcul de la contrainte admissible au cisaillement (Von Mises / Sécurité) [cite: 6, 13]
        sf.add_equation(
            "tau_adm", 
            r"\tau_{adm}", 
            "Re / (sqrt(3) * gamma_M)", 
            unit=u.MPa, 
            desc="Contrainte de cisaillement admissible",
            fmt=".2f"
        )

        # Calcul de la surface de cisaillement effective [cite: 13, 20]
        # A_cis = pi * d * Le * k_cis
        sf.add_equation(
            "A_cis", 
            "A_{cis}", 
            "pi * d * L_e * k_cis", 
            unit=u.mm**2, 
            desc="Surface de cisaillement efficace"
        )

        # Calcul de la contrainte de cisaillement réelle [cite: 6]
        sf.add_equation(
            "tau", 
            r"\tau", 
            "F_t / A_cis", 
            unit=u.MPa, 
            desc="Contrainte de cisaillement agissante",
            fmt=".2f"
        )

        # 4. Vérifications
        # Comparaison de la contrainte réelle vs admissible [cite: 7, 16]
        sf.add_check(
            "tau < tau_adm", 
            desc="Critère d'arrachement de filet", 
            name="Vérification"
        )

        # 5. Évaluation et Rapport
        sf.evaluate() # Calcul des valeurs [cite: 8]
        return sf.report() # Génération du LaTeX [cite: 9]

    mo.md(verifier_arrachement_filet())
    return


@app.cell
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
            unit=u.kN,   # Conversion automatique en kN 
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
    data = {'C':[85, 80], 'd':[16]*2, 'p':[2]*2, 'mu_th':[0.15]*2, 'mu_h':[0.15]*2}
    return (data,)


@app.cell
def _(calc_F0, data, pd):
    df = pd.DataFrame.from_dict(data)
    df2=df.assign(F0=calc_F0)
    df2
    return


@app.cell
def _(calc_F0, data):
    calc_F0(data)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

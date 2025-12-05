import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from simpleformbuilder import builder
    return builder, mo, np


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
def _():
    return


if __name__ == "__main__":
    app.run()

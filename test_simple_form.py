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


@app.cell
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


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

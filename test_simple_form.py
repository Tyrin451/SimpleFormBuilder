import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


app._unparsable_cell(
    r"""
    simport marimo as mo
    from builder import SimpleFormBuilder
    """,
    name="_"
)


@app.cell
def _(SimpleFormBuilder, mo):
    # 1. Initialisation
    builder = SimpleFormBuilder()
    u = builder.ureg

    # 2. Définition des paramètres
    builder.add_param("Fx", "F_x", 10 * u.kN, desc="Force axiale")
    builder.add_param("A", "A", 50 * u.cm**2, desc="Section")
    builder.add_param("sigma_a", r"\sigma_a", 100 * u.MPa, desc="Contrainte admissible")

    # 3. Définition des équations
    # sigma = Fx / A
    builder.add_equation("sigma", "\\sigma", "Fx / A", unit=u.MPa, desc="Contrainte")

    # 4. Ajout de vérifications (Checks)
    builder.add_check("sigma < sigma_a", desc="Contrainte admissible")

    # 5. Exécution des calculs
    print("Evaluation des calculs...")
    builder.evaluate()

    # 6. Génération du rapport
    print("Génération du rapport LaTeX...")
    report = builder.report()

    mo.md(f"$${report}$$")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

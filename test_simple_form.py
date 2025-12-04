import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from simpleformbuilder import builder
    return builder.SimpleFormBuilder, mo


@app.cell
def _(SimpleFormBuilder):
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
    builder.add_check("sigma <= sigma_a", desc="Contrainte admissible", name='Check1')

    # 5. Exécution des calculs
    builder.evaluate()

    templates = {
        "param": r"{symbol} &= {value} && \text{{{desc}}} \\",
        "eq": r"{symbol} &= {expr} = {value} && \text{{{desc}}} \\",
        "check": r"\text{{{name}}} : &&& \text{{{desc}}} \\ & {expr} \rightarrow {status} &&  \\"
    }
    # 6. Génération du rapport
    report = builder.report(row_templates=templates)
    return (report,)


@app.cell
def _(mo, report):
    mo.md(f"""
    $${report}$$
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

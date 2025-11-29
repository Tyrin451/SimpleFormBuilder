from builder import SimpleFormBuilder

def main():
    # 1. Initialisation
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    # 2. Définition des paramètres
    builder.add_param("Fx", "F_x", 10 * u.kN, desc="Force axiale")
    builder.add_param("A", "A", 50 * u.cm**2, desc="Section")
    
    # 3. Définition des équations
    # sigma = Fx / A
    builder.add_equation("sigma", "\\sigma", "Fx / A", unit=u.MPa, desc="Contrainte")
    
    # 4. Ajout de vérifications (Checks)
    # Critère : sigma < 235 MPa
    builder.add_check("sigma < 235 * u.MPa", desc="Critère Eurocode")
    
    # 5. Exécution des calculs
    print("Evaluation des calculs...")
    builder.evaluate()
    
    # 6. Génération du rapport
    print("Génération du rapport LaTeX...")
    report = builder.report()
    
    print("\n--- Rapport LaTeX ---\n")
    print(report)
    print("\n---------------------\n")

if __name__ == "__main__":
    main()

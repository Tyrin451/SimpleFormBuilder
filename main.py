from simpleformbuilder import builder

def main():
    # 1. Initialisation
    sf = builder.SimpleFormBuilder()
    u = sf.ureg
    
    # 2. Définition des paramètres
    sf.add_param("Fx", "F_x", 10 * u.kN, desc="Force axiale")
    sf.add_param("A", "A", 50 * u.cm**2, desc="Section")
    sf.add_param("sigma_a", r"\sigma_a", 100 * u.MPa, desc="Contrainte admissible")
    
    # 3. Définition des équations
    # sigma = Fx / A
    sf.add_equation("sigma", "\\sigma", "Fx / A", unit=u.MPa, desc="Contrainte")
    
    # 4. Ajout de vérifications (Checks)
    # Critère : sigma < 235 MPa
    sf.add_check("sigma < sigma_a", desc="Contrainte admissible")
    
    # 5. Exécution des calculs
    print("Evaluation des calculs...")
    sf.evaluate()
    
    # 6. Génération du rapport
    print("Génération du rapport LaTeX...")
    report = sf.report()
    
    print("\n--- Rapport LaTeX ---\n")
    print(report)
    print("\n---------------------\n")

if __name__ == "__main__":
    main()

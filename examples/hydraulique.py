from simpleformbuilder import builder
import numpy as np

# Initialisation
sf = builder.SimpleFormBuilder()
u = sf.ureg

# --- Paramètres Hydrauliques ---

# Débit volumique
sf.add_param("Q", "Q", 50 * u.liter / u.minute, desc="Débit volumique")

# Diamètre interne de la conduite
sf.add_param("D", "D", 25 * u.mm, desc="Diamètre interne")

# Longueur de la conduite
sf.add_param("L", "L", 100 * u.meter, desc="Longueur de la conduite")

# Propriétés du fluide (Eau à 20°C)
sf.add_param("rho", "\\rho", 998 * u.kg / u.m**3, desc="Masse volumique")
sf.add_param("mu", "\\mu", 1.002e-3 * u.Pa * u.s, desc="Viscosité dynamique")

# Rugosité absolue (Tuyau en acier commercial)
sf.add_param("epsilon", "\\epsilon", 0.045 * u.mm, desc="Rugosité absolue")

# --- Équations ---

# 1. Calcul de la vitesse moyenne
# v = Q / Section
# Section = pi * D^2 / 4
sf.add_equation("A", "A", "pi * D**2 / 4", unit=u.cm**2, desc="Section de passage")
sf.add_equation("v", "v", "Q / A", unit=u.m/u.s, desc="Vitesse moyenne d'écoulement")

# 2. Nombre de Reynolds
# Re = rho * v * D / mu
sf.add_equation("Re", "Re", "rho * v * D / mu", unit=u.dimensionless, desc="Nombre de Reynolds")

# 3. Calcul du facteur de friction (Darcy-Weisbach)
# Pour simplifier l'exemple, nous utilisons une formule explicite de Haaland (approximation de Colebrook-White)
# 1/sqrt(f) = -1.8 * log10( (epsilon/D/3.7)^1.11 + 6.9/Re )
# Note: SimpleFormBuilder utilise SymPy/NumPy, assurez-vous que les fonctions log/sqrt sont gérées.
# Pour simplifier ici si Re > 4000 (Turbulent) on utilise Blasius sinon Poiseuille (Laminaires).
# Mais faisons simple: on suppose un régime turbulent lisse pour cet exemple simple -> f = 0.316 / Re^0.25 (Blasius)
sf.add_equation("f", "f", "0.316 / Re**0.25", unit=u.dimensionless, desc="Facteur de friction (Blasius)")

# 4. Perte de charge linéaire
# DeltaP = f * (L/D) * (rho * v^2 / 2)
sf.add_equation("DeltaP", "\\Delta P", "f * (L / D) * (rho * v**2 / 2)", unit=u.bar, desc="Perte de charge")

# --- Vérifications ---

# Vérifier si l'écoulement est turbulent (Re > 4000)
sf.add_check("Re > 4000", desc="Régime Turbulent")

# Vérifier si la perte de charge est acceptable (< 5 bars)
sf.add_param("P_limit", "P_{lim}", 5 * u.bar, desc="Limite de perte de charge")
sf.add_check("DeltaP < P_limit", desc="Perte de charge acceptable")


# --- Génération ---
print("Calcul hydraulique...")
sf.evaluate()
print("\n--- Rapport Hydraulique ---")
print(sf.report())

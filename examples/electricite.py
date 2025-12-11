from simpleformbuilder import builder

# Initialisation
sf = builder.SimpleFormBuilder()
u = sf.ureg

# --- Paramètres Électriques ---
# Circuit simple : Source de tension + Pont diviseur résistif (R1 en série avec R2)

# Source de tension
sf.add_param("U_in", "U_{in}", 24 * u.volt, desc="Tension d'alimentation")

# Résistances
sf.add_param("R1", "R_1", 100 * u.ohm, desc="Résistance 1")
sf.add_param("R2", "R_2", 220 * u.ohm, desc="Résistance 2")

# Puissance max dissipable par les résistances
sf.add_param("P_max", "P_{max}", 2 * u.watt, desc="Puissance max des composants")

# --- Calculs ---

# 1. Résistance équivalente (Série)
sf.add_equation("R_eq", "R_{eq}", "R1 + R2", unit=u.ohm, desc="Résistance équivalente")

# 2. Courant total
# I = U / R
sf.add_equation("I", "I", "U_in / R_eq", unit=u.ampere, desc="Courant dans le circuit")

# 3. Tension aux bornes de R2 (Diviseur de tension)
# U2 = U_in * (R2 / (R1 + R2))
sf.add_equation("U2", "U_{R2}", "U_in * (R2 / R_eq)", unit=u.volt, desc="Tension aux bornes de R2")

# 4. Puissance dissipée par R1
# P1 = R1 * I^2
sf.add_equation("P1", "P_{R1}", "R1 * I**2", unit=u.watt, desc="Puissance dissipée par R1")

# 5. Puissance dissipée par R2
# P2 = U2^2 / R2
sf.add_equation("P2", "P_{R2}", "U2**2 / R2", unit=u.watt, desc="Puissance dissipée par R2")

# --- Vérifications ---

# Les résistances ne doivent pas griller
sf.add_check("P1 < P_max", desc="R1 supporte la puissance")
sf.add_check("P2 < P_max", desc="R2 supporte la puissance")

# --- Rapport ---
print("Calcul du circuit...")
sf.evaluate()
print("\n--- Rapport Électrique ---")
print(sf.report())

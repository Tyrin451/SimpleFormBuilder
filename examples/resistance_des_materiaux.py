from simpleformbuilder import builder

# Initialisation du constructeur
# Nous utilisons 'simpleformbuilder' pour créer une note de calcul structurée
sf = builder.SimpleFormBuilder()
u = sf.ureg  # Accès rapide aux unités (Pint)

# --- Paramètres d'entrée ---
# Définition des propriétés géométriques et mécaniques de la poutre
# Cas d'une poutre encastrée-libre (cantilever) soumise à une force ponctuelle à son extrémité

# Longueur de la poutre
sf.add_param("L", "L", 2.5 * u.meter, desc="Longueur de la poutre")

# Force appliquée à l'extrémité
sf.add_param("F", "F", 5000 * u.newton, desc="Force ponctuelle appliquée")

# Module de Young (Acier)
sf.add_param("E", "E", 210 * u.GPa, desc="Module de Young (Acier)")

# Moment quadratique (Inertie)
# Supposons une section rectangulaire b=10cm, h=20cm -> I = b*h^3/12
b = 10 * u.cm
h = 20 * u.cm
I_val = (b * h**3) / 12
sf.add_param("I", "I", I_val, desc="Moment quadratique de la section")

# Distance de la fibre neutre à la fibre extrême
sf.add_param("y_max", "y_{max}", h / 2, desc="Distance fibre neutre")

# Limite d'élasticité de l'acier
sf.add_param("sigma_e", "\\sigma_e", 235 * u.MPa, desc="Limite d'élasticité")

# --- Équations ---

# 1. Calcul du moment fléchissant maximum (à l'encastrement)
sf.add_equation("M_max", "M_{max}", "F * L", unit=u.kN * u.m, desc="Moment fléchissant max")

# 2. Calcul de la contrainte normale maximale (Flexion)
# Formule de Navier : sigma = M * y / I
sf.add_equation("sigma_max", "\\sigma_{max}", "M_max * y_max / I", unit=u.MPa, desc="Contrainte de flexion max")

# 3. Calcul de la flèche maximale (à l'extrémité libre)
# Pour une poutre cantilever : delta = F * L^3 / (3 * E * I)
sf.add_equation("delta_max", "\\delta_{max}", "(F * L**3) / (3 * E * I)", unit=u.mm, desc="Flèche maximale")

# --- Vérifications ---

# 1. Vérification de la résistance (Critère de Von Mises simplifié ou contrainte normale simple ici)
# On applique un coefficient de sécurité de 1.5 sur la limite élastique
sf.add_check("sigma_max < sigma_e / 1.5", desc="Vérification Résistance (Coeff 1.5)")

# 2. Vérification de la déformation (Critère de flèche)
# La flèche ne doit pas dépasser L/200
sf.add_check("delta_max < L / 200", desc="Vérification Flèche (L/200)")

# --- Génération du Rapport ---

print("Calcul en cours...")
sf.evaluate()

print("\n--- Résultat de la Note de Calcul (RDM) ---")
print(sf.report())

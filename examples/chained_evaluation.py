from simpleformbuilder import builder

# Initialize the builder
sf = builder.SimpleFormBuilder()

# Add Parameters
# Force F = 1000 N
sf.add_param("F", "F", 1000 * sf.ureg.newton, desc="Applied Force")

# Surface S = 10 cm^2
sf.add_param("S", "S", 10 * sf.ureg.cm**2, desc="Cross-sectional Area")

# Yield Strength Re = 200 MPa
sf.add_param("Re", "R_e", 200 * sf.ureg.MPa, desc="Yield Strength")

# Add Equations for Chained Evaluation

# 1. Calculate Stress sigma = F / S
# We expect the result in MPa
sf.add_equation("sigma", "\\sigma", "F / S", unit=sf.ureg.MPa, desc="Normal Stress")

# 2. Calculate Allowable Stress sigma_a = Re / 2
sf.add_equation("sigma_a", "\\sigma_a", "Re / 2", unit=sf.ureg.MPa, desc="Allowable Stress")

# 3. Calculate Load Ratio TC = sigma / sigma_a
# This depends on the previous two calculations
sf.add_equation("TC", "TC", "sigma / sigma_a", desc="Load Ratio")

# Evaluate all calculations
print("Evaluating calculations...")
sf.evaluate()

# Print results
print(f"Sigma: {sf['sigma']}")
print(f"Sigma_a: {sf['sigma_a']}")
print(f"TC: {sf['TC']}")

#print report
print("\n--- LaTeX Report ---")
report = sf.report()
print(report)
print("--------------------")
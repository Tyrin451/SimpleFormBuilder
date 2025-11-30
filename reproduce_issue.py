from builder import SimpleFormBuilder
import pint

def reproduce():
    builder = SimpleFormBuilder()
    
    builder.add_param("F_x", "F_x", 10.00 * builder.ureg.kN, "Force axiale")
    builder.add_param("A", "A", 50.00 * builder.ureg.cm**2, "Section")
    builder.add_param("sigma_a", "\sigma_a", 100.00 * builder.ureg.MPa, "Contrainte admissible")
    
    builder.add_equation("sigma", "\sigma", "F_x / A", unit=builder.ureg.MPa, desc="Contrainte")
    
    builder.add_check("sigma < sigma_a", "Contrainte admissible")
    
    builder.evaluate()
    print(builder.report())

if __name__ == "__main__":
    reproduce()

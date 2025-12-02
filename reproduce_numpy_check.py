
import numpy as np
from builder import SimpleFormBuilder

def reproduce():
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    # Define numpy vectors
    v1 = np.array([10, 20, 30])
    v2 = np.array([5, 15, 25])
    v3 = np.array([5, 25, 25]) # Second element 25 > 20, so v1 > v3 will be [True, False, True]

    builder.add_param("v1", "v_1", v1)
    builder.add_param("v2", "v_2", v2)
    builder.add_param("v3", "v_3", v3)

    # Check 1: Should be all True
    builder.add_check("all(v1 > v2)", desc="Check v1 > v2 (all)")
    
    # Check 2: Element-wise comparison (might fail)
    builder.add_check("v1 > v2", desc="Check v1 > v2 (element-wise)")

    try:
        builder.evaluate()
        print("Evaluation successful")
    except Exception as e:
        print(f"Evaluation failed: {e}")

    try:
        report = builder.report()
        print("Report generation successful")
        print(report)
    except Exception as e:
        print(f"Report generation failed: {e}")

if __name__ == "__main__":
    reproduce()

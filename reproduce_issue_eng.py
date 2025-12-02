from builder import SimpleFormBuilder
import pint

def check_eng_functions():
    builder = SimpleFormBuilder()
    u = builder.ureg
    
    builder.add_param("val1", "v1", -10)
    builder.add_param("val2", "v2", 20)
    
    try:
        builder.add_equation("abs_val", "abs_v", "abs(val1)")
        builder.evaluate()
        print(f"abs(val1) = {builder.params['abs_val']}")
    except Exception as e:
        print(f"abs(val1) failed: {e}")

    try:
        builder.add_equation("min_val", "min_v", "min(val1, val2)")
        builder.evaluate()
        print(f"min(val1, val2) = {builder.params['min_val']}")
    except Exception as e:
        print(f"min(val1, val2) failed: {e}")
        
    try:
        builder.add_equation("max_val", "max_v", "max(val1, val2)")
        builder.evaluate()
        print(f"max(val1, val2) = {builder.params['max_val']}")
    except Exception as e:
        print(f"max(val1, val2) failed: {e}")

if __name__ == "__main__":
    check_eng_functions()

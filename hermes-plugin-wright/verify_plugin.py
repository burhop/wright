import importlib.metadata
import sys
import os

def verify():
    print("Running Wright plugin skeleton verification...")

    # 1. Check if the package is installed and entry points are registered
    try:
        eps = importlib.metadata.entry_points(group='hermes_agent.plugins')
        wright_ep = next((ep for ep in eps if ep.name == 'wright'), None)
        
        if wright_ep is None:
            print("❌ entry_point 'wright' not found under group 'hermes_agent.plugins'.")
            print("Please make sure the package is installed in editable mode: pip install -e .")
            sys.exit(1)
            
        print(f"✅ Found entry point: {wright_ep.name} -> {wright_ep.value}")
        
        # 2. Try loading the entry point
        print("Loading entry point...")
        register_func = wright_ep.load()
        print("✅ Entry point loaded successfully.")
        
        # 3. Invoke registration
        print("Calling register()...")
        register_func(None)
        print("✅ register() executed successfully.")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify()

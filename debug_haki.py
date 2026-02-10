from src.haki_engine import create_engine
import sys

print("Starting debug...")
try:
    print("Creating engine...")
    engine = create_engine(force_rebuild=False)
    print("Engine created successfully.")
    print("Asking test question...")
    resp = engine.ask("Test question")
    print(f"Response: {resp}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

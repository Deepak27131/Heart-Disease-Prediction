
import sys
import traceback

try:
    print("Attempting to import app...")
    import app
    print("Import successful!")
except Exception:
    traceback.print_exc()

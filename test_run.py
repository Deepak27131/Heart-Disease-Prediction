
import sys
import traceback

log_file = "startup_log.txt"

def log(msg):
    with open(log_file, "a") as f:
        f.write(msg + "\n")

try:
    log("Starting test_run.py...")
    import app
    log("Import successful.")
    
    with app.app.app_context():
        log("Creating all tables...")
        app.db.create_all()
        log("Tables created.")
        
    log("Attempting to run app...")
    # Don't actually run, just check if we got here
    log("App run block reached successfully.")
    
except Exception:
    log("Error occurred:")
    with open(log_file, "a") as f:
        traceback.print_exc(file=f)

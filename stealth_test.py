import sys
import os
import traceback

# Redirect stdout and stderr immediately
sys.stdout = open("stealth_out.log", "w", encoding="utf-8")
sys.stderr = open("stealth_err.log", "w", encoding="utf-8")

try:
    import main
    print("Imported main successfully. Starting main.main()...")
    sys.stdout.flush()
    main.main()
except Exception as e:
    print(f"Exception occurred: {e}")
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()

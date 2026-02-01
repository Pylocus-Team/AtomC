import os
import sys
from atomc.console.console import run_tool, ensure_dirs

print(f"Current Working Directory: {os.getcwd()}")
print("Attempting to run ensure_dirs()...")
ensure_dirs()

if os.path.exists("build"):
    print("SUCCESS: 'build' directory exists.")
else:
    print("FAILURE: 'build' directory was NOT created.")

if os.path.exists("bin"):
    print("SUCCESS: 'bin' directory exists.")
else:
    print("FAILURE: 'bin' directory was NOT created.")

print("\n--- Testing rxc rewrite logic ---")
# Simulate user typing: rxc atomc/examples/factorial.ryx -o factorial.ro
args = ["atomc/examples/factorial.ryx", "-o", "factorial.ro"]
print(f"Input args: {args}")

# We'll hijack print to capture output
print("\nRunning rxc via console logic...")
# Note: we are calling run_tool directly to see if it makes the file
ret = run_tool("rxc", args)
print(f"Return code: {ret}")

print("\nChecking if build/factorial.ro exists...")
if os.path.exists("build/factorial.ro"):
    print("SUCCESS: build/factorial.ro FOUND.")
else:
    print("FAILURE: build/factorial.ro NOT FOUND.")
    # Check if it ended up somewhere else
    if os.path.exists("factorial.ro"):
        print("Wait! It was found in root (factorial.ro), not in build/!")

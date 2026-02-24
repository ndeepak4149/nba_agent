import sys

print("--- AI ENGINEERING SYSTEM CHECK ---")
print(f"Python Version: {sys.version.split()[0]}")
print("Loading libraries...")

try:
    import langchain
    import nba_api
    import wikipedia
    print("✅ SUCCESS: All AI libraries are installed and ready.")
    print("We are ready to build the NBA Agent.")
except ImportError as e:
    print(f"❌ ERROR: Missing library -> {e}")

print("-----------------------------------")
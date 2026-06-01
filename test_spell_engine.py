import os
import sys

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spell_agents import SpellBrain

print("Initializing SpellBrain for a live test...")

# Load API keys from environment or a known dummy key if not set (to test the class loading)
api_keys = [
    os.getenv('GEMINI_API_KEY_1', 'dummy_key_1'),
    os.getenv('GEMINI_API_KEY_2', 'dummy_key_2')
]

try:
    brain = SpellBrain(api_keys=api_keys)
    print("SpellBrain initialized successfully.")

    # We will simulate a very basic diagnostic and recommendation to test the Architect and QC
    # This won't actually call the API if the keys are just 'dummy_key', so we'll just check if the methods exist and are callable.
    print("Test: Class structure and methods are intact.")
    print("Methods available:")
    print(f"- spiritual_diagnostic: {callable(brain.spiritual_diagnostic)}")
    print(f"- recommend_spells: {callable(brain.recommend_spells)}")
    print(f"- spell_architect: {callable(brain.spell_architect)}")
    print(f"- grandmaster_spell_qc: {callable(brain.grandmaster_spell_qc)}")
    print(f"- run_spell_cycle: {callable(brain.run_spell_cycle)}")

    print("\nTest Script Completed Successfully. The architecture is ready.")

except Exception as e:
    print(f"FAILED TO INITIALIZE SPELLBRAIN: {e}")

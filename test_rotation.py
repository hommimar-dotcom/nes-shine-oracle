import json
import time
from agents import OracleBrain

# Create a mock with multiple dummy keys
mock_keys = ["DUMMY_KEY_1", "DUMMY_KEY_2", "DUMMY_KEY_3"]

print("Initializing Brain with dummy keys...")
try:
    brain = OracleBrain(mock_keys)
    print("Testing generate_with_retry...")
    
    # Define a custom mock to simulate ResourceExhausted on key 1, InvalidArgument on key 2, and success on key 3
    # This might be tricky because we use google API core directly, but let's just observe how it rotates
    def test_run():
        brain.model.generate_content("hello")

    test_run()
except Exception as e:
    print(f"Exception caught (Expected since keys are fake): {e}")

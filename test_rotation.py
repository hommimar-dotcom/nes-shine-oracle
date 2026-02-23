import sys
from unittest.mock import MagicMock
from google.api_core import exceptions
from agents import OracleBrain

def test_rotation():
    keys = ["KEY_1_EXHAUSTED", "KEY_2_EXHAUSTED", "KEY_3_VALID"]
    brain = OracleBrain(keys)
    
    call_count = {"count": 0}
    
    def mock_generate_content(*args, **kwargs):
        call_count["count"] += 1
        current_key = brain.api_keys[brain.current_key_index]
        print(f"\n[API Call {call_count['count']}] Attempting with Key: {current_key}")
        
        if current_key == "KEY_1_EXHAUSTED" or current_key == "KEY_2_EXHAUSTED":
            print(f"-> MOCK: Simulating 429 ResourceExhausted for {current_key}...")
            raise exceptions.ResourceExhausted("Simulated 429 quota exceed")
        
        print("-> MOCK: Success! Returning mock response.")
        mock_resp = MagicMock()
        mock_resp.text = "SUCCESS DATA"
        mock_resp.usage_metadata = None
        return mock_resp

    # We must patch _reinit_models so it re-injects our mock after recreating the objects
    original_reinit = brain._reinit_models
    def patched_reinit():
        original_reinit()
        brain.model.generate_content = mock_generate_content
        brain.extraction_model.generate_content = mock_generate_content
    
    brain._reinit_models = patched_reinit
    brain.model.generate_content = mock_generate_content
    
    print("--- STARTING ROTATION TEST ---")
    
    try:
        res = brain.generate_with_retry(brain.model, "Test Prompt")
        print("\n--- TEST COMPLETE ---")
        print(f"Final output: {res.text}")
        print(f"Final Active Key Index: {brain.current_key_index} ({brain.api_keys[brain.current_key_index]})")
    except Exception as e:
        print(f"\nCRITICAL FAILURE DURING ROTATION: {e}")

if __name__ == "__main__":
    test_rotation()

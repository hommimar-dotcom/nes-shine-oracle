import time
import google.generativeai as genai
from google.api_core import exceptions

def retry_api_call(func, retries=3, delay=2, backoff=2):
    """
    Wraps an API call with a retry mechanism for Rate Limit (429) errors.
    """
    for i in range(retries):
        try:
            return func()
        except exceptions.ResourceExhausted as e:
            if i == retries - 1:
                raise e # Give up after last retry
            
            wait_time = delay * (backoff ** i)
            print(f"Rate limit hit. Retrying in {wait_time} seconds... (Attempt {i+1}/{retries})")
            time.sleep(wait_time)
        except Exception as e:
            # Reraise other errors immediately
            raise e
            
def safe_generate_content(model, prompt):
    """
    Safe wrapper for model.generate_content using the retry logic.
    """
    return retry_api_call(lambda: model.generate_content(prompt))

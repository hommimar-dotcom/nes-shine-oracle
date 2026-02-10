import os
import time
import google.generativeai as genai
from google.api_core import exceptions

def create_pdf(html_content: str, filename: str):
    """
    Saves the HTML content as an HTML file (PDF generation via Playwright
    has compatibility issues with Python 3.14).
    The HTML file can be opened in a browser and printed to PDF.
    """
    output_dir = "saved_readings"
    os.makedirs(output_dir, exist_ok=True)
    
    # Change extension from .pdf to .html
    html_filename = filename.replace('.pdf', '.html')
    file_path = os.path.join(output_dir, html_filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return file_path

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


import os

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

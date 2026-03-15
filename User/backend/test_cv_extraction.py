import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.document.processor import extract_text_from_pdf

def test():
    pdf_path = "Venuka Sirimanne CV Updated.pdf"
    if not os.path.exists(pdf_path):
        print(f"File {pdf_path} not found.")
        return
        
    with open(pdf_path, "rb") as f:
        content = f.read()
        
    print("Testing extract_text_from_pdf on CV...")
    try:
        text = extract_text_from_pdf(content, filename=pdf_path)
        print(f"Extracted {len(text)} characters.")
        print(f"First 500 chars: {text[:500]}")
    except Exception as e:
        print(f"Error extracting text: {e}")

if __name__ == "__main__":
    test()

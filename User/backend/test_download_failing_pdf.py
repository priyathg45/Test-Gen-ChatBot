import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.utils.mongo import get_database
from src.config import config
from src.document.attachments import get_attachment_file

def download_pdfs():
    print("Downloading 0-length PDFs...")
    try:
        db = get_database(config.MONGO_URI, config.MONGO_DB)
        coll = db[config.MONGO_ATTACHMENTS_COLLECTION]
        attachments = list(coll.find({}).sort("created_at", -1))
        
        for att in attachments:
            length = len(att.get('extracted_text', ''))
            if length == 0 and att.get('filename', '').endswith('.pdf'):
                print(f"Downloading {att['filename']}...")
                file_bytes = get_attachment_file(db, att)
                if file_bytes:
                    safe_name = att['filename'].replace('/', '_').replace(':', '_')
                    with open(safe_name, 'wb') as f:
                        f.write(file_bytes)
                    print(f"Saved {safe_name}")
                break # Just download one to test
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_pdfs()

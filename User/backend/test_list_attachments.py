import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.utils.mongo import get_database
from src.config import config

def check_attachments():
    print("Checking ALL attachments in MongoDB...")
    try:
        db = get_database(config.MONGO_URI, config.MONGO_DB)
        coll = db[config.MONGO_ATTACHMENTS_COLLECTION]
        attachments = list(coll.find({}).sort("created_at", -1))
        
        zero_lengths = []
        for att in attachments:
            length = len(att.get('extracted_text', ''))
            print(f"File: {att.get('filename')}, Type: {att.get('content_type')}, Length: {length}, Session: {att.get('session_id')}")
            if length == 0:
                zero_lengths.append(att)
                
        print(f"\nTotal attachments with 0 length: {len(zero_lengths)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_attachments()

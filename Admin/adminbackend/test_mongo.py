import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.config import Config
from src.utils.mongo import get_collection

try:
    print(f"Connecting to: {Config.MONGO_URI}")
    users_col = get_collection(Config.MONGO_URI, Config.MONGO_DB, "users")
    if users_col is not None:
        users = list(users_col.find({}))
        print(f"SUCCESS: Found {len(users)} users.")
        for u in users:
            print(u.get('email', 'no email'))
    else:
        print("FAIL: users_col is None")
except Exception as e:
    print(f"ERROR: {e}")

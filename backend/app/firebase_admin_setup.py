import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage
from app.config import FIREBASE_CRED_PATH

# 1. Try to fetch the credentials JSON string from Render's Environment Variable
firebase_json_str = os.environ.get('FIREBASE_CONFIG_JSON')

if firebase_json_str:
    # If found (on Render), parse the raw JSON string into a dictionary
    cred_dict = json.loads(firebase_json_str)
    cred = credentials.Certificate(cred_dict)
else:
    # If not found (locally on your machine), use your existing config path
    cred = credentials.Certificate(FIREBASE_CRED_PATH)

# 2. Initialize the app with the credentials and your storage bucket
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "storageBucket": "employee-record-6ef30.firebasestorage.app"
    })

# 3. Export your database instance as before
db = firestore.client()
import os
from dotenv import load_dotenv

load_dotenv()

FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "./employee-record-6ef30-firebase-adminsdk-fbsvc-e1219622cc.json")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
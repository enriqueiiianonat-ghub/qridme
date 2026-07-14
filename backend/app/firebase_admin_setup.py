import firebase_admin
from firebase_admin import credentials, firestore, storage
from app.config import FIREBASE_CRED_PATH

cred = credentials.Certificate(FIREBASE_CRED_PATH)
firebase_admin.initialize_app(cred, {
    "storageBucket": "employee-record-6ef30.firebasestorage.app"
})

db = firestore.client()
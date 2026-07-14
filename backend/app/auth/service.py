from fastapi import HTTPException
from firebase_admin import auth as firebase_auth
from app.firebase_admin_setup import db
from datetime import datetime, timezone

def verify_id_token(id_token: str) -> dict:
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def create_or_update_profile(uid: str, first_name: str, family_name: str, email: str) -> dict:
    doc_ref = db.collection("profiles").document(uid)
    data = {
        "first_name": first_name,
        "family_name": family_name,
        "email": email,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    doc_ref.set(data, merge=True)
    return {"uid": uid, **data}

def get_profile(uid: str) -> dict:
    doc = db.collection("profiles").document(uid).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"uid": uid, **doc.to_dict()}
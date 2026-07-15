import random
import time
import resend
from fastapi import HTTPException
from app.firebase_admin_setup import db
from app.config import RESEND_API_KEY

resend.api_key = RESEND_API_KEY

OTP_VALIDITY_SECONDS = 600  # 10 minutes

def generate_and_send_otp(uid: str, email: str) -> None:
    otp_code = f"{random.randint(100000, 999999)}"

    db.collection("email_otps").document(uid).set({
        "otp_code": otp_code,
        "email": email,
        "created_at": time.time(),
        "verified": False,
    })

    email_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>QRIDME — Email Verification</h2>
        <p>Your verification code is:</p>
        <div style="font-size: 30px; font-weight: bold; padding: 20px; background: #f2f2f2; text-align: center; letter-spacing: 5px;">
            {otp_code}
        </div>
        <p>This code expires in 10 minutes. If you didn't request this, you can ignore this email.</p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": "no-reply@qridme.com",
            "to": email,
            "subject": "QRIDME - Verify Your Email",
            "html": email_html,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send verification email: {str(e)}")


def verify_otp(uid: str, otp_code: str) -> bool:
    doc_ref = db.collection("email_otps").document(uid)
    snap = doc_ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="No verification request found. Please request a new code.")

    data = snap.to_dict()

    age_seconds = time.time() - data.get("created_at", 0)
    if age_seconds > OTP_VALIDITY_SECONDS:
        raise HTTPException(status_code=400, detail="Verification code expired. Please request a new one.")

    if data.get("otp_code") != otp_code.strip():
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    doc_ref.update({"verified": True})

    db.collection("profiles").document(uid).update({"email_verified": True})
    return True


def is_email_verified(uid: str) -> bool:
    profile_doc = db.collection("profiles").document(uid).get()
    if not profile_doc.exists:
        return False
    return profile_doc.to_dict().get("email_verified", False)
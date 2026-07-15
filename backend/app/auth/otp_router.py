from fastapi import APIRouter, Depends
from app.auth.otp_schemas import SendOtpRequest, VerifyOtpRequest
from app.auth.otp_service import generate_and_send_otp, verify_otp
from app.auth.router import get_current_uid

router = APIRouter(prefix="/auth", tags=["auth-otp"])

@router.post("/send-otp")
def send_otp(payload: SendOtpRequest, uid: str = Depends(get_current_uid)):
    generate_and_send_otp(payload.uid, payload.email)
    return {"message": "Verification code sent to your email."}

@router.post("/verify-otp")
def verify_otp_endpoint(payload: VerifyOtpRequest, uid: str = Depends(get_current_uid)):
    verify_otp(payload.uid, payload.otp_code)
    return {"message": "Email verified successfully."}
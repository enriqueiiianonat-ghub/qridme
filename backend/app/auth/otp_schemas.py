from pydantic import BaseModel

class SendOtpRequest(BaseModel):
    uid: str
    email: str

class VerifyOtpRequest(BaseModel):
    uid: str
    otp_code: str
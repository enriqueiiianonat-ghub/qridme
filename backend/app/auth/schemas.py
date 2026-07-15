from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterProfileRequest(BaseModel):
    id_token: str
    first_name: str
    family_name: str
    email: EmailStr

class ProfileResponse(BaseModel):
    uid: str
    first_name: str
    family_name: str
    email: EmailStr
    created_at: Optional[str] = None
    email_verified: Optional[bool] = False
from fastapi import APIRouter, Depends, Header, HTTPException
from app.auth.schemas import RegisterProfileRequest, ProfileResponse
from app.auth.service import verify_id_token, create_or_update_profile, get_profile

router = APIRouter(prefix="/auth", tags=["auth"])

def get_current_uid(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    decoded = verify_id_token(token)
    return decoded["uid"]

@router.post("/register-profile", response_model=ProfileResponse)
def register_profile(payload: RegisterProfileRequest):
    decoded = verify_id_token(payload.id_token)
    if decoded.get("email") != payload.email:
        raise HTTPException(status_code=400, detail="Email mismatch with token")
    profile = create_or_update_profile(
        uid=decoded["uid"],
        first_name=payload.first_name,
        family_name=payload.family_name,
        email=payload.email,
    )
    return profile

@router.get("/me", response_model=ProfileResponse)
def read_me(uid: str = Depends(get_current_uid)):
    return get_profile(uid)
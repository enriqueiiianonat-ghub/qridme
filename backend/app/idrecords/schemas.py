from pydantic import BaseModel
from typing import Optional

class IDRecordOut(BaseModel):
    record_id: str
    uid: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    suffix: Optional[str] = None
    sex_gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    place_of_birth: Optional[str] = None
    complete_address: Optional[str] = None
    city_municipality: Optional[str] = None
    state_province_region: Optional[str] = None
    postal_zip_code: Optional[str] = None
    country: Optional[str] = None
    mobile_phone_number: Optional[str] = None
    email_address: Optional[str] = None
    qr_image_base64: Optional[str] = None
    qr_level: Optional[str] = "basic"
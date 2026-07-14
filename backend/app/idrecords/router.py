from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException
from typing import Optional
from app.auth.router import get_current_uid
from app.idrecords.storage import upload_file_to_storage, delete_all_user_files
from app.idrecords.service import (
    create_id_record, get_id_record, get_id_record_by_uid,
    update_id_record, delete_id_record,
)
from app.idrecords.schemas import IDRecordOut

router = APIRouter(prefix="/id-records", tags=["id-records"])


async def id_record_form(
    first_name: str = Form(...),
    middle_name: Optional[str] = Form(None),
    last_name: str = Form(...),
    suffix: Optional[str] = Form(None),
    sex_gender: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    place_of_birth: Optional[str] = Form(None),
    complete_address: Optional[str] = Form(None),
    unit_house_building_number: Optional[str] = Form(None),
    street_name: Optional[str] = Form(None),
    subdivision_district_barangay: Optional[str] = Form(None),
    city_municipality: Optional[str] = Form(None),
    state_province_region: Optional[str] = Form(None),
    postal_zip_code: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    marital_status: Optional[str] = Form(None),
    spouse_name: Optional[str] = Form(None),
    parents_names: Optional[str] = Form(None),
    mobile_phone_number: Optional[str] = Form(None),
    email_address: Optional[str] = Form(None),
    occupation: Optional[str] = Form(None),
    education_level: Optional[str] = Form(None),
    nationality_citizenship_status: Optional[str] = Form(None),
    religion: Optional[str] = Form(None),
    blood_type: Optional[str] = Form(None),
    parent_guardian_information: Optional[str] = Form(None),
    qr_level: str = Form("basic"),  # "basic" or "advanced"
    id_photo: Optional[UploadFile] = File(None),
    birth_certificate: Optional[UploadFile] = File(None),
    passport: Optional[UploadFile] = File(None),
    drivers_license: Optional[UploadFile] = File(None),
    existing_national_id: Optional[UploadFile] = File(None),
    citizenship_certificate: Optional[UploadFile] = File(None),
    utility_bills: Optional[UploadFile] = File(None),
    bank_statements: Optional[UploadFile] = File(None),
    lease_agreement: Optional[UploadFile] = File(None),
    government_issued_correspondence: Optional[UploadFile] = File(None),
    fingerprints: Optional[UploadFile] = File(None),
    facial_photograph: Optional[UploadFile] = File(None),
    guardians_id: Optional[UploadFile] = File(None),
    birth_certificate_required: Optional[UploadFile] = File(None),
    visa_or_residence_permit: Optional[UploadFile] = File(None),
    immigration_documents: Optional[UploadFile] = File(None),
):
    fields = {
        "first_name": first_name, "middle_name": middle_name, "last_name": last_name,
        "suffix": suffix, "sex_gender": sex_gender, "date_of_birth": date_of_birth,
        "place_of_birth": place_of_birth, "complete_address": complete_address,
        "unit_house_building_number": unit_house_building_number, "street_name": street_name,
        "subdivision_district_barangay": subdivision_district_barangay,
        "city_municipality": city_municipality, "state_province_region": state_province_region,
        "postal_zip_code": postal_zip_code, "country": country,
        "marital_status": marital_status, "spouse_name": spouse_name,
        "parents_names": parents_names, "mobile_phone_number": mobile_phone_number,
        "email_address": email_address, "occupation": occupation,
        "education_level": education_level,
        "nationality_citizenship_status": nationality_citizenship_status,
        "religion": religion, "blood_type": blood_type,
        "parent_guardian_information": parent_guardian_information,

       
    }
    
    
    files = {
        "id_photo": id_photo, "birth_certificate": birth_certificate, "passport": passport,
        "drivers_license": drivers_license, "existing_national_id": existing_national_id,
        "citizenship_certificate": citizenship_certificate, "utility_bills": utility_bills,
        "bank_statements": bank_statements, "lease_agreement": lease_agreement,
        "government_issued_correspondence": government_issued_correspondence,
        "fingerprints": fingerprints, "facial_photograph": facial_photograph,
        "guardians_id": guardians_id, "birth_certificate_required": birth_certificate_required,
        "visa_or_residence_permit": visa_or_residence_permit,
        "immigration_documents": immigration_documents,
    }
    return {"fields": fields, "files": files, "qr_level": qr_level}


def _upload_files(uid: str, files: dict) -> dict:
    file_urls = {}
    for category, upload in files.items():
        if upload is not None:
            file_urls[category] = upload_file_to_storage(uid, category, upload)
    return file_urls


@router.post("", response_model=IDRecordOut)
async def submit_id_record(uid: str = Depends(get_current_uid), form=Depends(id_record_form)):
    existing = get_id_record_by_uid(uid)
    if existing:
        raise HTTPException(status_code=409, detail="Record already exists. Use PUT /id-records/me to update.")
    file_urls = _upload_files(uid, form["files"])
    record = create_id_record(uid, form["fields"], file_urls, form["qr_level"])
    return record


@router.get("/me", response_model=IDRecordOut)
def read_my_id_record(uid: str = Depends(get_current_uid)):
    record = get_id_record_by_uid(uid)
    if not record:
        raise HTTPException(status_code=404, detail="No record found")
    return record


@router.put("/me", response_model=IDRecordOut)
async def update_my_id_record(uid: str = Depends(get_current_uid), form=Depends(id_record_form)):
    existing = get_id_record_by_uid(uid)
    if not existing:
        raise HTTPException(status_code=404, detail="No existing record. Use POST /id-records to create one.")
    file_urls = _upload_files(uid, form["files"])
    updated = update_id_record(existing["record_id"], form["fields"], file_urls, form["qr_level"])
    return updated


@router.delete("/me")
def delete_my_id_record(uid: str = Depends(get_current_uid)):
    existing = get_id_record_by_uid(uid)
    if not existing:
        raise HTTPException(status_code=404, detail="No record found")
    delete_all_user_files(uid)
    delete_id_record(existing["record_id"])
    return {"detail": "Record deleted"}


@router.get("/{record_id}", response_model=IDRecordOut)
def read_id_record(record_id: str):
    record = get_id_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record
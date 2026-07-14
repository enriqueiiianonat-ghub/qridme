import uuid
from datetime import datetime, timezone
from app.firebase_admin_setup import db
from app.idrecords.qr_utils import generate_qr_base64

BASIC_QR_FIELDS = [
    "record_id", "first_name", "middle_name", "last_name", "suffix",
    "sex_gender", "complete_address", "city_municipality",
    "state_province_region", "country", "mobile_phone_number",
]

ADVANCED_QR_FIELDS = BASIC_QR_FIELDS + [
    "date_of_birth", "place_of_birth", "postal_zip_code",
    "marital_status", "spouse_name", "parents_names", "email_address",
    "occupation", "education_level", "nationality_citizenship_status",
    "religion", "blood_type", "parent_guardian_information",
    "has_birth_certificate", "has_passport", "has_drivers_license",
    "has_existing_national_id", "has_citizenship_certificate",
    "has_utility_bills", "has_bank_statements", "has_lease_agreement",
    "has_government_issued_correspondence", "has_fingerprints",
    "has_facial_photograph", "has_guardians_id",
    "has_visa_or_residence_permit", "has_immigration_documents",
]

def _qr_fields_for_level(record: dict, level: str) -> dict:
    field_list = ADVANCED_QR_FIELDS if level == "advanced" else BASIC_QR_FIELDS
    payload = {}
    for key in field_list:
        if key.startswith("has_"):
            file_key = key[4:]
            payload[key] = bool(record.get("file_urls", {}).get(file_key))
        elif record.get(key):
            payload[key] = record.get(key)
    return payload

def create_id_record(uid: str, form_data: dict, file_urls: dict, qr_level: str = "basic") -> dict:
    record_id = uuid.uuid4().hex[:12].upper()

    record = {
        "record_id": record_id,
        "uid": uid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "qr_level": qr_level,
        **form_data,
        "file_urls": file_urls,
    }

    db.collection("id_records").document(record_id).set(record)

    qr_payload = _qr_fields_for_level(record, qr_level)
    qr_b64 = generate_qr_base64(qr_payload)

    db.collection("id_records").document(record_id).update({"qr_image_base64": qr_b64})
    record["qr_image_base64"] = qr_b64
    return record

def get_id_record(record_id: str) -> dict:
    doc = db.collection("id_records").document(record_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()

def get_id_record_by_uid(uid: str) -> dict:
    query = db.collection("id_records").where("uid", "==", uid).limit(1).stream()
    for doc in query:
        return doc.to_dict()
    return None

def update_id_record(record_id: str, form_data: dict, new_file_urls: dict, qr_level: str = "basic") -> dict:
    doc_ref = db.collection("id_records").document(record_id)
    existing = doc_ref.get().to_dict() or {}

    merged_files = {**existing.get("file_urls", {}), **new_file_urls}
    update_payload = {
        **form_data,
        "file_urls": merged_files,
        "qr_level": qr_level,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    doc_ref.update(update_payload)

    updated = doc_ref.get().to_dict()
    qr_payload = _qr_fields_for_level(updated, qr_level)
    qr_b64 = generate_qr_base64(qr_payload)
    doc_ref.update({"qr_image_base64": qr_b64})
    updated["qr_image_base64"] = qr_b64
    return updated

def delete_id_record(record_id: str) -> None:
    db.collection("id_records").document(record_id).delete()
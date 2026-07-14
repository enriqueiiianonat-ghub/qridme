import uuid
from firebase_admin import storage as fb_storage
from fastapi import UploadFile

def upload_file_to_storage(uid: str, category: str, file: UploadFile) -> str:
    """Uploads a file to Firebase Storage under uploads/{uid}/{category}/{uuid}_filename
    Returns the public download URL (or storage path if you prefer signed URLs)."""
    bucket = fb_storage.bucket()
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    blob_path = f"uploads/{uid}/{category}/{uuid.uuid4().hex}.{ext}"
    blob = bucket.blob(blob_path)
    blob.upload_from_file(file.file, content_type=file.content_type)
    blob.make_public()  # simplest option for dev; use signed URLs in production
    return blob.public_url

def delete_all_user_files(uid: str) -> None:
    bucket = fb_storage.bucket()
    blobs = bucket.list_blobs(prefix=f"uploads/{uid}/")
    for blob in blobs:
        blob.delete()
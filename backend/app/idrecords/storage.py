import io
import uuid
from firebase_admin import storage as fb_storage
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps

MAX_PDF_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB — comfortably covers a 2-4 page scanned document
MAX_IMAGE_DIMENSION = 1600  # px, long edge — plenty sharp for ID verification, much smaller file size
IMAGE_JPEG_QUALITY = 75

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "bmp", "gif"}


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else ""


def _compress_image(file_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(file_bytes))
    img = ImageOps.exif_transpose(img)  # fixes phone photos that appear sideways
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=IMAGE_JPEG_QUALITY, optimize=True)
    return output.getvalue()


def upload_file_to_storage(uid: str, category: str, file: UploadFile) -> str:
    bucket = fb_storage.bucket()
    original_name = file.filename or "upload"
    ext = _get_extension(original_name)
    content_type = (file.content_type or "").lower()

    file.file.seek(0)
    raw_bytes = file.file.read()

    is_pdf = ext == "pdf" or content_type == "application/pdf"
    is_image = ext in IMAGE_EXTENSIONS or content_type.startswith("image/")

    if is_pdf:
        if len(raw_bytes) > MAX_PDF_SIZE_BYTES:
            size_mb = len(raw_bytes) / (1024 * 1024)
            limit_mb = MAX_PDF_SIZE_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=(
                    f"'{category}' PDF is {size_mb:.1f}MB, which exceeds the {limit_mb}MB limit. "
                    "Please upload a smaller scan — a 2-4 page document should comfortably fit."
                ),
            )
        blob_path = f"uploads/{uid}/{category}/{uuid.uuid4().hex}.pdf"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(raw_bytes, content_type="application/pdf")
        blob.make_public()
        return blob.public_url

    if is_image:
        try:
            compressed_bytes = _compress_image(raw_bytes)
        except Exception:
            # If the file can't be decoded as an image for some reason,
            # fall back to uploading the original bytes rather than failing outright.
            compressed_bytes = raw_bytes
        blob_path = f"uploads/{uid}/{category}/{uuid.uuid4().hex}.jpg"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(compressed_bytes, content_type="image/jpeg")
        blob.make_public()
        return blob.public_url

    # Fallback for any other file type — upload as-is
    blob_path = f"uploads/{uid}/{category}/{uuid.uuid4().hex}_{original_name}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(raw_bytes, content_type=content_type or "application/octet-stream")
    blob.make_public()
    return blob.public_url


def delete_all_user_files(uid: str) -> None:
    bucket = fb_storage.bucket()
    blobs = bucket.list_blobs(prefix=f"uploads/{uid}/")
    for blob in blobs:
        blob.delete()
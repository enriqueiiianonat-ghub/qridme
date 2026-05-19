import requests
import urllib.parse
import mimetypes
import uuid

DB_URL = "https://employee-record-6ef30-default-rtdb.asia-southeast1.firebasedatabase.app"
STORAGE_BUCKET = "employee-record-6ef30.firebasestorage.app"

def delete_file_from_storage(file_url):
    try:
        # Extracts the raw path buried between '/o/' and the query token '?'
        if "/o/" not in file_url:
            print("Invalid URL format for storage deletion mapping.")
            return False
            
        raw_path = file_url.split("/o/")[1].split("?")[0]
        # Decodes HTTP path characters (e.g., converting %2F back to forward slashes /)
        decoded_storage_path = urllib.parse.unquote(raw_path)
        
        encoded_delete_path = urllib.parse.quote(decoded_storage_path, safe='')
        url = f"https://firebasestorage.googleapis.com/v0/b/{STORAGE_BUCKET}/o/{encoded_delete_path}"
        
        response = requests.delete(url)
        if response.status_code == 204:
            print(f"Successfully purged file from Storage: {decoded_storage_path}")
            return True
        else:
            print(f"Firebase Storage deletion rejected (Status: {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print("Delete error exception loop:", e)
        return False

def upload_file_web(file_bytes, destination_path):
    encoded_path = urllib.parse.quote(destination_path, safe='')
    upload_url = f"https://firebasestorage.googleapis.com/v0/b/{STORAGE_BUCKET}/o?name={encoded_path}"
    headers = {"Content-Type": "application/octet-stream"}
    response = requests.post(upload_url, data=file_bytes, headers=headers)
    
    if response.status_code == 200:
        return f"https://firebasestorage.googleapis.com/v0/b/{STORAGE_BUCKET}/o/{encoded_path}?alt=media"
    else:
        print(f"Upload failed: {response.text}")
        return None

def get_db():
    return DB_URL

def upload_file(file_bytes, destination_path):
    encoded_path = urllib.parse.quote(destination_path, safe="")
    upload_url = f"https://firebasestorage.googleapis.com/v0/b/{STORAGE_BUCKET}/o?uploadType=media&name={encoded_path}"
    headers = {"Content-Type": "application/octet-stream"}
    response = requests.post(upload_url, data=file_bytes, headers=headers)

    if response.status_code in [200, 201]:
        return f"https://firebasestorage.googleapis.com/v0/b/{STORAGE_BUCKET}/o/{encoded_path}?alt=media"
    raise Exception(f"Firebase upload failed: {response.text}")

def extract_storage_path(url):
    try:
        if "/o/" not in url: return url
        path = url.split("/o/")[1].split("?")[0]
        return urllib.parse.unquote(path)
    except:
        return None

def delete_file_from_storage_placeholder(file_url_or_path):
    print(f"REST delete requested for: {file_url_or_path}")

def delete_user_folder(user_id):
    print(f"REST folder delete requested for: {user_id}")

# This is the function your main.py calls!
# ==========================================
# ORGANIZED FILE ATTACHMENT STORAGE ROUTING
# ==========================================
def upload_bytes(file_bytes, original_name, user_email, document_type):
    try:
        ext = original_name.split(".")[-1] if "." in original_name else "bin"
        unique_name = f"{uuid.uuid4()}.{ext}"
        
        # Cleans email format to create a safe folder path string
        safe_email_folder = user_email.replace(".", "_")
        safe_doc_type_folder = document_type.lower().replace(" ", "_")
        
        # STRUCTURED ARCHITECTURE: uploads/user_email/document_type/unique_name
        destination_path = f"uploads/{safe_email_folder}/{safe_doc_type_folder}/{unique_name}"
        encoded_path = urllib.parse.quote(destination_path, safe="")

        upload_url = (
            f"https://firebasestorage.googleapis.com/v0/b/"
            f"{STORAGE_BUCKET}/o?uploadType=media&name={encoded_path}"
        )

        content_type = (
            mimetypes.guess_type(original_name)[0]
            or "application/octet-stream"
        )

        headers = {
            "Content-Type": content_type
        }

        response = requests.post(upload_url, data=file_bytes, headers=headers)

        if response.status_code not in [200, 201]:
            print("Firebase upload failed logs:", response.text)
            return None

        response_data = response.json()
        download_token = response_data.get("downloadTokens")

        if download_token:
            file_url = (
                f"https://firebasestorage.googleapis.com/v0/b/"
                f"{STORAGE_BUCKET}/o/{encoded_path}?alt=media&token={download_token}"
            )
        else:
            file_url = (
                f"https://firebasestorage.googleapis.com/v0/b/"
                f"{STORAGE_BUCKET}/o/{encoded_path}?alt=media"
            )

        return file_url

    except Exception as e:
        print("Firebase upload error:", e)
        return None
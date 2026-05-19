from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import database
import firebase
import uuid
import requests
import hashlib

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FIREBASE_API_KEY = "AIzaSyDYPePzsumtH9EqplYOaw1kTP2PKXo6Qic"  # Ensure your valid web API key is here
DB_URL = "https://employee-record-6ef30-default-rtdb.asia-southeast1.firebasedatabase.app"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class DeleteDocRequest(BaseModel):
    email: str
    doc_id: str
    download_url: str

# ==========================================
# REGISTRATION & AUTHENTICATION ENDPOINTS
# ==========================================
@app.post("/register")
async def register_user(
    email: str = Form(...), 
    password: str = Form(...),
    first_name: str = Form(...),
    family_name: str = Form(...)
):
    email_clean = email.strip().lower()
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
        
    signup_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    signup_payload = {"email": email_clean, "password": password, "returnSecureToken": True}
    
    signup_response = requests.post(signup_url, json=signup_payload)
    signup_data = signup_response.json()
    
    if signup_response.status_code != 200:
        error_msg = signup_data.get("error", {}).get("message", "Registration failed.")
        raise HTTPException(status_code=400, detail=f"Auth Error: {error_msg}")
    
    id_token = signup_data.get("idToken")
    
    update_profile_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FIREBASE_API_KEY}"
    display_name_bundle = f"{first_name.strip()}|||{family_name.strip()}"
    requests.post(update_profile_url, json={
        "idToken": id_token,
        "displayName": display_name_bundle,
        "returnSecureToken": False
    })
    
    verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    requests.post(verify_url, json={"requestType": "VERIFY_EMAIL", "idToken": id_token})
    
    return {"message": "Account created! Please check your email inbox to verify your account before logging in."}


@app.post("/login")
async def login_user(email: str = Form(...), password: str = Form(...)):
    email_clean = email.strip().lower()
    
    login_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    login_response = requests.post(login_url, json={"email": email_clean, "password": password, "returnSecureToken": True})
    login_data = login_response.json()
    
    if login_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid credentials.")
        
    id_token = login_data.get("idToken")
    profile_response = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}", 
        json={"idToken": id_token}
    )
    user_info = profile_response.json().get("users", [{}])[0]
    
    if not user_info.get("emailVerified", False):
        raise HTTPException(status_code=403, detail="Access Denied: Please verify your email address first.")
        
    safe_email_key = email_clean.replace(".", "_")
    db_profile = database.get_user(safe_email_key)
    
    if not db_profile:
        display_name_bundle = user_info.get("displayName", "|||")
        names_split = display_name_bundle.split("|||")
        
        first_name_extracted = names_split[0] if len(names_split) > 0 else ""
        family_name_extracted = names_split[1] if len(names_split) > 1 else ""
        
        db_profile = {
            "email": email_clean,
            "first_name": first_name_extracted,
            "family_name": family_name_extracted,
            "address": "",       # Initialize blank parameters
            "birthday": "",      # Initialize blank parameters
            "uid": user_info.get("localId"),
            "documents": {}
        }
        database.save_user(safe_email_key, db_profile)
        
    return {
        "message": "Login successful!",
        "email": email_clean,
        "first_name": db_profile.get("first_name", ""),
        "family_name": db_profile.get("family_name", "") or "",
        "address": db_profile.get("address", ""),       # NEW: Return field data
        "birthday": db_profile.get("birthday", ""),     # NEW: Return field data
        "documents": db_profile.get("documents", {})
    }


# ==========================================
# UPDATED: ACCEPTS NEW PROFILE PARAMETERS
# ==========================================
@app.post("/update-profile")
def update_profile_names(
    email: str = Form(...), 
    first_name: str = Form(...), 
    family_name: str = Form(...),
    address: str = Form(...),      # NEW Field Ingestion
    birthday: str = Form(...)      # NEW Field Ingestion
):
    try:
        safe_email_key = email.strip().lower().replace(".", "_")
        database.save_user(f"{safe_email_key}/first_name", first_name.strip())
        database.save_user(f"{safe_email_key}/family_name", family_name.strip())
        database.save_user(f"{safe_email_key}/address", address.strip())      # Save to DB
        database.save_user(f"{safe_email_key}/birthday", birthday.strip())    # Save to DB
        return {
            "message": "Identity parameters updated successfully inside database!",
            "first_name": first_name.strip(),
            "family_name": family_name.strip(),
            "address": address.strip(),
            "birthday": birthday.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-documents")
def get_user_documents(email: str):
    safe_email_key = email.strip().lower().replace(".", "_")
    user_profile = database.get_user(safe_email_key) or {}
    return {"documents": user_profile.get("documents", {})}


@app.post("/upload")
@app.post("/upload/")
async def upload_document_to_user_node(
    email: str = Form(...),               
    document_type: str = Form(...),       
    file: UploadFile = File(...)
):
    try:
        file_bytes = await file.read()
        original_name = file.filename
        
        storage_url = firebase.upload_bytes(file_bytes, original_name, email, document_type)
        if not storage_url:
            return {"message": "Process Aborted: Storage injection failed."}
            
        doc_id = f"doc_{str(uuid.uuid4())[:8]}"
        document_metadata = {
            "file_name": original_name,
            "download_url": storage_url,
            "document_type": document_type
        }
        
        safe_email_key = email.strip().lower().replace(".", "_")
        database.save_user(f"{safe_email_key}/documents/{doc_id}", document_metadata)
        
        return {
            "message": "Document uploaded successfully!",
            "url": storage_url
        }
    except Exception as e:
        return {"message": f"Pipeline execution failed: {str(e)}"}


@app.post("/delete-document")
def delete_user_document(req: DeleteDocRequest):
    try:
        firebase.delete_file_from_storage(req.download_url)
        safe_email_key = req.email.strip().lower().replace(".", "_")
        rest_db_url = f"{DB_URL}/users/{safe_email_key}/documents/{req.doc_id}.json"
        requests.delete(rest_db_url)
        return {"message": "Document successfully dropped!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/delete-account")
async def remove_entire_user_profile_and_auth(email: str = Form(...), password: str = Form(...)):
    try:
        email_clean = email.strip().lower()
        login_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
        login_response = requests.post(login_url, json={"email": email_clean, "password": password, "returnSecureToken": True})
        
        if login_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Authentication verification failed. Incorrect password.")
            
        id_token = login_response.json().get("idToken")
        delete_auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={FIREBASE_API_KEY}"
        requests.post(delete_auth_url, json={"idToken": id_token})
        
        safe_email_key = email_clean.replace(".", "_")
        profile_data = database.get_user(safe_email_key) or {}
        documents_map = profile_data.get("documents", {})
        
        for doc_key in documents_map:
            doc_item = documents_map[doc_key]
            if "download_url" in doc_item:
                firebase.delete_file_from_storage(doc_item["download_url"])
                
        rest_account_url = f"{DB_URL}/users/{safe_email_key}.json"
        requests.delete(rest_account_url)
        return {"message": "Account completely deleted."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
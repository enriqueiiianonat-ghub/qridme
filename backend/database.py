import requests
import urllib.parse

# This must match your Realtime Database URL exactly
DB_URL = "https://employee-record-6ef30-default-rtdb.asia-southeast1.firebasedatabase.app"

def get_safe_url(user_id):
    # Encodes special characters like '@' to '%40' for the URL path
    safe_id = urllib.parse.quote(user_id)
    return f"{DB_URL}/users/{safe_id}.json"

def save_user(user_id, data):
    url = get_safe_url(user_id)
    response = requests.put(url, json=data)
    return response.json()

def update_user(user_id, data):
    url = get_safe_url(user_id)
    response = requests.patch(url, json=data)
    return response.json()

def get_user(user_id):
    url = get_safe_url(user_id)
    response = requests.get(url)
    data = response.json()
    # Returns empty dict if user doesn't exist
    return data if data is not None else {}

def delete_user(user_id: str):
    url = get_safe_url(user_id)
    response = requests.delete(url)
    return response.status_code == 200
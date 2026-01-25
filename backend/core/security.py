import os
import json
import secrets
import uuid
from fastapi import Depends, HTTPException, status, Header
from core.config import settings

SECRETS_FILE = os.path.join(settings.CONFIG_DIR, "secrets.json")

# In-memory session store: { "token_uuid": "username" }
# Note: This resets on container restart. For persistence, we'd need a DB/File.
ACTIVE_SESSIONS = {}

def get_stored_credentials():
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "username": os.getenv("ADMIN_USER", "admin"),
        "password": os.getenv("ADMIN_PASS", "admin")
    }

def save_credentials(username, password):
    os.makedirs(settings.CONFIG_DIR, exist_ok=True)
    with open(SECRETS_FILE, 'w') as f:
        json.dump({"username": username, "password": password}, f)

# --- New Login Logic ---
def login_user(username, password):
    stored = get_stored_credentials()
    if (secrets.compare_digest(username, stored["username"]) and 
        secrets.compare_digest(password, stored["password"])):
        
        # Generate Token
        token = str(uuid.uuid4())
        ACTIVE_SESSIONS[token] = username
        return token
    return None

def logout_user(token):
    if token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]

# --- Dependency for Protected Routes ---
def validate_auth(x_auth_token: str = Header(None)):
    if not x_auth_token or x_auth_token not in ACTIVE_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing session token"
        )
    return ACTIVE_SESSIONS[x_auth_token]

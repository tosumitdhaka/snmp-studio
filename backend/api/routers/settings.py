import secrets
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from core.security import save_credentials, validate_auth, login_user, logout_user, get_stored_credentials

router = APIRouter(prefix="/settings", tags=["Settings"])

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthUpdate(BaseModel):
    current_password: str
    username: str
    password: str

# NEW: Login Endpoint (Public)
@router.post("/login")
def login(creds: LoginRequest):
    token = login_user(creds.username, creds.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": token, "username": creds.username}

# NEW: Logout Endpoint
@router.post("/logout")
def logout(x_auth_token: str = Depends(validate_auth)):
    logout_user(x_auth_token)
    return {"status": "logged_out"}

@router.get("/check")
def check_auth_status(username: str = Depends(validate_auth)):
    return {"status": "authenticated", "user": username}

@router.post("/auth", dependencies=[Depends(validate_auth)])
def update_auth(creds: AuthUpdate):
    # 1. Verify Current Password
    stored = get_stored_credentials()
    if not secrets.compare_digest(creds.current_password, stored["password"]):
        raise HTTPException(status_code=403, detail="Current password incorrect")

    # 2. Save New Credentials
    save_credentials(creds.username, creds.password)
    return {"status": "updated", "message": "Credentials updated. Please log in again."}
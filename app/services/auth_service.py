import os
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

supabase: Client = create_client(supabase_url, supabase_key)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)
        if response and response.user:
            return response.user
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication credentials: {str(e)}")

def register_user(email: str, password: str, nickname: str):
    try:
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if auth_response.user:
            user_data = supabase.table("users").insert({
                "id": auth_response.user.id,
                "email": email,
                "nickname": nickname,
                "login_type": "email"
            }).execute()

            logger.info(f"User data insert response: {user_data}")

            return {
                "message": "User registered successfully",
                "user_id": auth_response.user.id
            }
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def login_user(email: str, password: str):
    try:
        logger.info(f"Attempting login for email: {email}")
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        logger.info(f"Auth response: {auth_response}")

        if auth_response.user and auth_response.session:
            return {
                "message": "Login successful",
                "access_token": auth_response.session.access_token,
                "user_id": auth_response.user.id
            }
        else:
            logger.info("Login failed: User or session not found in auth response")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail="Login failed")

def social_login(provider: str, request: Request):
    try:
        callback_url = str(request.base_url) + "auth/callback"
        logger.info(f"Callback URL: {callback_url}")
        auth_response = supabase.auth.sign_in_with_oauth({
            "provider": provider,
            "options": {
                "redirect_to": callback_url
            }
        })

        logger.info(f"Auth response: {auth_response}")
        if hasattr(auth_response, 'url'):
            return {"url": auth_response.url}
        else:
            raise HTTPException(status_code=400, detail="OAuth initialization failed")
    except Exception as e:
        logger.error(f"Social Login Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Social login error: {str(e)}")

# 기존의 auth_callback 함수도 여기로 옮깁니다.
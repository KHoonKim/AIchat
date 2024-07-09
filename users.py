import os
import logging
import json
from typing import List, Optional, Literal  
from dotenv import load_dotenv
from enum import Enum

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



router = APIRouter()
logger = logging.getLogger(__name__)

# Provider를 직접 정의합니다
class SocialProvider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"
    APPLE = "apple"
    AZURE = "azure"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    DISCORD = "discord"
    # 필요한 다른 제공자들을 여기에 추가하세요


class SocialLoginData(BaseModel):
    provider: Literal["google", "github", "facebook"]  # 지원하는 제공자 목록


load_dotenv()

app = FastAPI()
router = APIRouter()
security = HTTPBearer()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

supabase: Client = create_client(supabase_url, supabase_key)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    nickname: str = Field(..., min_length=2, max_length=50)


class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=2, max_length=50)
    profile_image_url: Optional[str] = None


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    nickname: str
    profile_image_url: Optional[str]
    login_type: str


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)
        if response and response.user:
            return response.user
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication credentials: {str(e)}")


@router.post("/register")
async def register_user(user: UserCreate):
    try:
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })

        if auth_response.user:
            user_data = supabase.table("users").insert({
                "id": auth_response.user.id,
                "email": user.email,
                "nickname": user.nickname,
                "login_type": "email"
            }).execute()

            print(f"User data insert response: {user_data}")  # 디버깅을 위한 로그

            return {
                "message": "User registered successfully",
                "user_id": auth_response.user.id
            }
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
    except Exception as e:
        print(f"Registration error: {str(e)}")  # 디버깅을 위한 로그
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login_user(email: str, password: str):
    try:
        print(f"Attempting login for email: {email}")  # 디버깅을 위한 로그
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        print(f"Auth response: {auth_response}")  # 디버깅을 위한 로그

        if auth_response.user and auth_response.session:
            return {
                "message": "Login successful",
                "access_token": auth_response.session.access_token,
                "user_id": auth_response.user.id
            }
        else:
            print("Login failed: User or session not found in auth response")  # 디버깅을 위한 로그
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        print(f"Login error: {str(e)}")  # 디버깅을 위한 로그
        raise HTTPException(status_code=401, detail="Login failed")
        

@router.post("/social-login")
async def social_login(login_data: SocialLoginData, request: Request):
    try:
        callback_url = str(request.base_url) + "auth/callback"  # '/users' 제거
        print(f"Callback URL: {callback_url}")  # 디버깅을 위한 로그
        auth_response = supabase.auth.sign_in_with_oauth({
            "provider": login_data.provider,
            "options": {
                "redirect_to": callback_url
            }
        })

        print(f"Auth response: {auth_response}")  # 디버깅을 위한 로그
        if hasattr(auth_response, 'url'):
            return {"url": auth_response.url}
        else:
            raise HTTPException(status_code=400, detail="OAuth initialization failed")
    except Exception as e:
        print(f"Social Login Error: {str(e)}")  # 디버깅을 위한 로그
        raise HTTPException(status_code=400, detail=f"Social login error: {str(e)}")




@router.get("/auth/callback")
async def auth_callback(code: Optional[str] = None, error: Optional[str] = None, request: Request = None):
    logger.info(f"Auth callback called. Code: {code}, Error: {error}")
    
    if error:
        logger.error(f"OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code:
        logger.error("No code provided")
        raise HTTPException(status_code=400, detail="No code provided")
    if code is None:
        if 'test' in request.query_params:
            # 테스트 모드
            code = 'test_code'
            logger.info("Test mode activated, using test_code")
        else:
            logger.error("No code provided")
            raise HTTPException(status_code=400, detail="No code provided")
    logger.info(f"Received code: {code}")


    
    try:
        supabase: Client = request.app.state.supabase
        
        # 테스트 코드 ('test' 코드에 대한 처리)
        if code == 'test':
            logger.info("Test code detected. Returning mock response.")
            return {
                "message": "Test auth callback successful",
                "access_token": "test_token",
                "user": {
                    "id": "test_user_id",
                    "email": "test@example.com",
                    "nickname": "TestUser"
                }
            }
        
        auth_response = supabase.auth.exchange_code_for_session(code)
        logger.info(f"Auth response type: {type(auth_response)}")
        logger.info(f"Auth response content: {auth_response}")
        
        if isinstance(auth_response, str):
            try:
                auth_response = json.loads(auth_response)
            except json.JSONDecodeError:
                logger.error("Failed to parse auth_response as JSON")
                raise HTTPException(status_code=500, detail="Failed to parse authentication response")
        
        if isinstance(auth_response, dict):
            session = auth_response.get('session', {})
            user = auth_response.get('user', {})
        elif hasattr(auth_response, 'session') and hasattr(auth_response, 'user'):
            session = auth_response.session
            user = auth_response.user
        else:
            logger.error(f"Unexpected auth_response structure: {auth_response}")
            raise HTTPException(status_code=500, detail="Unexpected response structure from authentication service")

        if not user or not session:
            logger.error("User or session information is missing")
            raise HTTPException(status_code=400, detail="User or session information is missing")

        # 사용자 정보 조회 또는 생성
        user_id = user.get('id') if isinstance(user, dict) else getattr(user, 'id', None)
        user_email = user.get('email') if isinstance(user, dict) else getattr(user, 'email', None)
        
        if not user_id or not user_email:
            logger.error("User ID or email is missing")
            raise HTTPException(status_code=400, detail="User ID or email is missing")

        user_data = supabase.table("users").select("*").eq("id", user_id).single().execute()
        
        if not user_data.data:
            # 새 사용자 생성
            new_user = {
                "id": user_id,
                "email": user_email,
                "nickname": f"User_{user_id[:8]}",  # 기본 닉네임 설정
                "login_type": "social"
            }
            insert_result = supabase.table("users").insert(new_user).execute()
            if not insert_result.data:
                logger.error("Failed to create new user")
                raise HTTPException(status_code=500, detail="Failed to create new user")
            logger.info(f"New user created: {user_email}")
            user_nickname = new_user["nickname"]
        else:
            logger.info(f"Existing user logged in: {user_email}")
            user_nickname = user_data.data.get("nickname", f"User_{user_id[:8]}")

        access_token = session.get('access_token') if isinstance(session, dict) else getattr(session, 'access_token', None)
        if not access_token:
            logger.error("Access token is missing")
            raise HTTPException(status_code=400, detail="Access token is missing")

        return {
            "message": "Social login successful",
            "access_token": access_token,
            "user": {
                "id": user_id,
                "email": user_email,
                "nickname": user_nickname
            }
        }
    except Exception as e:
        logger.exception(f"Error in auth callback: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing authentication: {str(e)}")


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(user=Depends(get_current_user)):
    try:
        user_data = supabase.table("users").select("*").eq("id", user.id).single().execute()
        if user_data and user_data.get("data"):
            return UserProfile(**user_data["data"])
        else:
            raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(user_update: UserUpdate, user=Depends(get_current_user)):
    try:
        update_data = user_update.dict(exclude_unset=True)
        user_data = supabase.table("users").update(update_data).eq("id", user.id).execute()
        if user_data and user_data.get("data"):
            return UserProfile(**user_data["data"][0])
        else:
            raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
async def logout_user(user=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/linked-accounts", response_model=List[str])
async def get_linked_accounts(user=Depends(get_current_user)):
    try:
        user_data = supabase.table("users").select("login_type").eq("id", user.id).execute()
        if user_data and user_data.get("data"):
            return [user_data["data"][0]['login_type']]
        else:
            return []
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app.include_router(router)
import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import create_client, Client


router = APIRouter()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

supabase: Client = create_client(supabase_url, supabase_key)

security = HTTPBearer()

class User(BaseModel):
    id: str
    email: str
    is_admin: bool = False  # is_admin 필드 추가


def get_supabase_token(email: str, password: str) -> str:
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response and response.session:
            return response.session.access_token
        else:
            raise HTTPException(status_code=401, detail="Unable to authenticate with Supabase")
    except Exception as e:
        print(f"Supabase Auth Error: {str(e)}")
        raise HTTPException(status_code=401, detail="Supabase authentication error")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)
        if response and response.user:
            # is_admin 정보를 가져오는 로직 추가
            user_data = supabase.table("users").select("is_admin").eq("id", response.user.id).single().execute()
            is_admin = user_data.data.get('is_admin', False) if user_data.data else False
            return User(id=response.user.id, email=response.user.email, is_admin=is_admin)  # is_admin 추가
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
                "login_type": "email",
                "is_admin": False  # 기본적으로 새 사용자는 관리자가 아님
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
            logger.error("Login failed: User or session not found in auth response")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        if "Invalid login credentials" in str(e):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        elif "Email not confirmed" in str(e):
            raise HTTPException(status_code=401, detail="Email not confirmed. Please check your email for verification link.")
        else:
            raise HTTPException(status_code=401, detail="Login failed. Please try again.")

def social_login(provider: str, request: Request):
    try:
        callback_url = "http://localhost:8000/auth/callback"
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

async def auth_callback(request: Request):
    try:
        logger.debug("Auth callback hit")
        code = request.query_params.get('code')
        error = request.query_params.get('error')
        logger.debug(f"Received code: {code}, error: {error}")


        # URL 프래그먼트를 처리하기 위한 HTML 응답
        html_content = """
        <html>
        <body>
            <script>
                function sendTokenToServer() {
                    var hash = window.location.hash.substring(1);
                    var params = new URLSearchParams(hash);
                    var access_token = params.get('access_token');

                    if (!access_token) {
                        document.body.innerHTML = '<h1>Error: No access token found</h1>';
                        return;
                    }

                    fetch('/process_token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({access_token: access_token}),
                    })
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(err => {
                                throw new Error(err.detail || 'Unknown error occurred');
                            });
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.message && data.user_id) {
                            document.body.innerHTML = `<h1>${data.message}</h1><p>User ID: ${data.user_id}</p>`;
                            setTimeout(() => {
                                window.location.href = '/';
                            }, 2000);  // Redirect back to the original page after 3 seconds
                        } else {
                            throw new Error('Invalid response data');
                        }
                    })
                    .catch((error) => {
                        console.error('Error:', error);
                        document.body.innerHTML = '<h1>Error occurred during authentication</h1><p>' + error.message + '</p>';
                    });
                }
                window.onload = sendTokenToServer;
            </script>
            <h1>Processing authentication...</h1>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.exception(f"Error in auth_callback: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing authentication: {str(e)}")


async def process_token(token_data: dict):
    try:
        access_token = token_data.get('access_token')
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token not provided")

        # 액세스 토큰을 사용하여 사용자 정보 가져오기
        user = supabase.auth.get_user(access_token)
        
        if not user or not user.user:
            raise HTTPException(status_code=400, detail="User information not found")
        
        user_id = user.user.id
        user_email = user.user.email
        
        # 사용자 정보 조회
        user_data = supabase.table("users").select("*").eq("id", user_id).execute()
        logger.debug(f"User data: {user_data}")
        
        if user_data.data:
            # 기존 사용자
            message = f"Successfully logged in."
            logger.debug(f"Existing user logged in: {user_id}")
        else:
            # 신규 사용자 생성
            new_user = {
                "id": user_id,
                "email": user_email,
                "nickname": f"User_{user_id[:8]}",
                "login_type": "social",
                "is_admin": False  # 새 사용자는 기본적으로 관리자가 아님
            }
            insert_result = supabase.table("users").insert(new_user).execute()
            logger.debug(f"Insert result: {insert_result}")
            if not insert_result.data:
                raise HTTPException(status_code=500, detail="Failed to create new user")
            message = f"New user successfully created."
            logger.debug(f"New user created: {user_id}")
        
        response_data = {
            "message": message,
            "user_id": user_id
        }
        logger.debug(f"Returning response: {response_data}")
        return response_data
    
    except Exception as e:
        logger.exception(f"Detailed error in process_token: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing authentication: {str(e)}")

async def get_user_profile(user: User = Depends(get_current_user)):
    try:
        logger.debug(f"Fetching profile for user ID: {user.id}")
        user_data = supabase.table("users").select("*").eq("id", user.id).single().execute()
        if user_data.data:
            logger.debug(f"User data retrieved: {user_data.data}")
            # is_admin 정보를 포함하여 반환
            return {**user_data.data, "is_admin": user.is_admin}
        else:
            logger.error("User profile not found")
            raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def update_user_profile(user_update, user):
    try:
        update_data = user_update.dict(exclude_unset=True)
        user_data = supabase.table("users").update(update_data).eq("id", user.id).execute()
        if user_data and user_data.get("data"):
            return user_data["data"][0]
        else:
            raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def logout_user():
    try:
        supabase.auth.sign_out()
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def get_linked_accounts(user):
    try:
        user_data = supabase.table("users").select("login_type").eq("id", user.id).execute()
        if user_data and user_data.get("data"):
            return [user_data["data"][0]['login_type']]
        else:
            return []
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
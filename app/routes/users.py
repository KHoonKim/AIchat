from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from app.models.user import UserCreate, UserUpdate, UserProfile
from app.services.auth_service import get_current_user, register_user, login_user, social_login, auth_callback

router = APIRouter()

@router.post("/register")
async def register(user: UserCreate):
    return register_user(user.email, user.password, user.nickname)

@router.post("/login")
async def login(email: str, password: str):
    return login_user(email, password)

@router.post("/social-login")
async def social_login_route(login_data: SocialLoginData, request: Request):
    return social_login(login_data.provider, request)

@router.get("/auth/callback")
async def auth_callback_route(code: Optional[str] = None, error: Optional[str] = None, request: Request = None):
    return auth_callback(code, error, request)

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(user=Depends(get_current_user)):
    # 프로필 조회 로직
    pass

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(user_update: UserUpdate, user=Depends(get_current_user)):
    # 프로필 업데이트 로직
    pass

@router.post("/logout")
async def logout_user(user=Depends(get_current_user)):
    # 로그아웃 로직
    pass

@router.get("/linked-accounts")
async def get_linked_accounts(user=Depends(get_current_user)):
    # 연결된 계정 조회 로직
    pass
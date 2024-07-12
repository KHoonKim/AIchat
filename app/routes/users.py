from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Optional, List
from app.models.user import UserCreate, UserUpdate, UserProfile, SocialLoginData
from app.services.auth_service import (
    get_current_user, process_token, register_user, login_user, social_login, auth_callback,
    get_user_profile, update_user_profile, logout_user, get_linked_accounts
)

router = APIRouter()

@router.post("/register")
async def register(user: UserCreate):
    try:
        result = register_user(user.email, user.password, user.nickname)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(email: str, password: str):
    try:
        result = login_user(email, password)
        return result
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/social-login")
async def social_login_route(login_data: SocialLoginData, request: Request):
    return social_login(login_data.provider, request)

@router.get("/auth/callback")
async def auth_callback_route(request: Request):
    return await auth_callback(request)

@router.post("/process_token")
async def process_token_route(token_data: dict):
    return await process_token(token_data)

@router.get("/profile", response_model=UserProfile)
async def get_profile(user=Depends(get_current_user)):
    return await get_user_profile(user)

@router.put("/profile", response_model=UserProfile)
async def update_profile(user_update: UserUpdate, user=Depends(get_current_user)):
    return await update_user_profile(user_update, user)

@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    return await logout_user()

@router.get("/linked-accounts", response_model=List[str])
async def linked_accounts(user=Depends(get_current_user)):
    return await get_linked_accounts(user)
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.models.user import UserBase, UserCreate, UserProfile, UserUpdate
from app.services.auth_service import (auth_callback, get_current_user,
                                       get_linked_accounts, get_user_profile,
                                       login_user, logout_user, process_token,
                                       register_user, social_login,
                                       update_user_profile)

router = APIRouter()

@router.post("/register")
async def register(user: UserCreate):
    try:
        result = register_user(user.email, user.password, user.nickname)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class UserBase(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(user: UserBase):
    try:
        result = login_user(user.email, user.password)
        return result
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/social-login/{provider}")
async def social_login_route(provider: str, request: Request):
    try:
        response = social_login(provider, request)
        return JSONResponse(content=response)
    except HTTPException as e:
        return JSONResponse(content={"detail": e.detail}, status_code=e.status_code)

@router.get("/auth/callback")
async def auth_callback_route(request: Request):
    return await auth_callback(request)

@router.post("/process_token")
async def process_token_route(token_data: dict):
    try:
        response = await process_token(token_data)
        return JSONResponse(content=response)
    except HTTPException as e:
        return JSONResponse(content={"detail": e.detail}, status_code=e.status_code)

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
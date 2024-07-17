from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal

class UserBase(BaseModel):
    email: EmailStr
    nickname: str = Field(..., min_length=2, max_length=50)
    is_admin: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=2, max_length=50)
    profile_image_url: Optional[str] = None
    is_admin: Optional[bool] = None

class SocialLoginData(BaseModel):
    provider: Literal["google", "kakao"]

class UserInDB(UserBase):
    id: str
    hashed_password: str
    login_type: str = "email"
    profile_image_url: Optional[str] = None

class UserProfile(UserBase):
    id: str
    profile_image_url: Optional[str]
    login_type: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
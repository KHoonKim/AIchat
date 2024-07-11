from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    nickname: str = Field(..., min_length=2, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=2, max_length=50)
    profile_image_url: Optional[str] = None

class UserInDB(UserBase):
    id: str
    hashed_password: str
    login_type: str = "email"
    profile_image_url: Optional[str] = None

class UserProfile(UserBase):
    id: str
    profile_image_url: Optional[str]
    login_type: str

# Config 클래스를 사용하여 ORM 모드 활성화
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
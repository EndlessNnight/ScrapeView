from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class AuthTokenData(BaseModel):
    token: str
    refreshToken: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class RegisterResponseData(BaseModel):
    id: int
    username: str
    email: str

class UserInfoData(BaseModel):
    userId: str
    userName: str
    roles: List[str]
    buttons: List[str]

class AuthLogin(BaseModel):
    userName: str
    password: str

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True 

class RefreshToken(BaseModel):
    refresh_token: str

class AuthRefreshToken(BaseModel):
    refreshToken: str

class ErrorResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None

class UserSettingBase(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None

class UserSettingCreate(UserSettingBase):
    pass

class UserSettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None

class UserSetting(UserSettingBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

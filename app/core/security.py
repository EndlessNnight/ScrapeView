from datetime import datetime, timedelta, UTC
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from passlib.context import CryptContext
from app.schemas.user import TokenData
from app.schemas.douyin import ApiResponse
from fastapi.responses import JSONResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        # 刷新token的有效期设置为7天
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def verify_refresh_token(token: str):
    """验证刷新token
    
    Args:
        token: 刷新token字符串
        
    Returns:
        成功返回用户名，失败返回None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        expire_time = payload.get("exp")
        
        # 检查token是否过期
        if expire_time is None or datetime.fromtimestamp(expire_time, UTC) < datetime.now(UTC):
            return None
            
        if username is None or token_type != "refresh":
            return None
            
        return username
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 自定义Token失效的响应格式
    token_exception = HTTPException(
        status_code=status.HTTP_200_OK,
        detail=ApiResponse(
            code=9999,
            message="Token已失效，请重新登录",
            data=None
        ).model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise token_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise token_exception
    
    from app.crud.user import get_user_by_username
    from app.db.session import base_db
    
    with base_db.get_db() as session:
        user = get_user_by_username(session, username=token_data.username)
        if user is None:
            raise token_exception
        return user 
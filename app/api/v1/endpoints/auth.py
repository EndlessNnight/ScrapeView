from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.crud import user as user_crud
from app.schemas.user import UserCreate, UserResponse, Token, RefreshToken, AuthLogin, AuthTokenData, RegisterResponseData, UserInfoData, AuthRefreshToken
from app.schemas.douyin import ApiResponse
from app.core.security import create_access_token, get_current_user, create_refresh_token, verify_refresh_token
from app.db.session import get_db
from app.crud.user import create_user, get_user_by_email, get_user_by_username
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=ApiResponse[RegisterResponseData])
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 检查邮箱是否已存在
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 创建新用户
    new_user = create_user(db, user)
    
    # 创建响应数据
    response_data = RegisterResponseData(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email
    )
    
    # 返回ApiResponse格式的响应
    return ApiResponse(
        code=200,
        message="注册成功",
        data=response_data
    )

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = user_crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/auth/login", response_model=ApiResponse[AuthTokenData])
async def auth_login(
    login_data: AuthLogin,
    db: Session = Depends(get_db)
):
    """使用JSON格式登录，参数为userName和password"""
    # 将userName映射到username参数
    username = login_data.userName
    password = login_data.password
    
    user = user_crud.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # 创建符合要求的响应格式
    token_data = AuthTokenData(token=access_token, refreshToken=refresh_token)
    return ApiResponse(code=200, message="登录成功", data=token_data)

@router.post("/refresh", response_model=ApiResponse[AuthTokenData])
async def refresh_token(refresh_token: RefreshToken):
    """使用刷新token获取新的访问token"""
    username = await verify_refresh_token(refresh_token.refresh_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=ApiResponse(
                code=9999,
                message="刷新token已失效，请重新登录",
                data=None
            ).model_dump()
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": username})
    
    # 创建符合要求的响应格式
    token_data = AuthTokenData(token=access_token, refreshToken=new_refresh_token)
    return ApiResponse(code=200, message="刷新token成功", data=token_data)

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user 

@router.get("/auth/getUserInfo", response_model=ApiResponse[UserInfoData])
async def get_user_info(current_user = Depends(get_current_user)):
    """获取用户信息，包括角色和权限按钮"""
    # 创建用户信息响应数据
    user_info = UserInfoData(
        userId=str(current_user.id),
        userName=current_user.username,
        roles=["R_SUPER"],  # 目前固定值
        buttons=["B_CODE1", "B_CODE2", "B_CODE3"]  # 目前固定值
    )
    
    # 返回ApiResponse格式的响应
    return ApiResponse(
        code=200,
        message="获取用户信息成功",
        data=user_info
    )

@router.post("/auth/refreshToken", response_model=ApiResponse[AuthTokenData])
async def auth_refresh_token(refresh_token: AuthRefreshToken):
    """使用刷新token获取新的访问token，返回ApiResponse格式"""
    username = await verify_refresh_token(refresh_token.refreshToken)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=ApiResponse(
                code=9999,
                message="刷新token已失效，请重新登录",
                data=None
            ).model_dump()
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": username})
    
    # 创建符合要求的响应格式
    token_data = AuthTokenData(token=access_token, refreshToken=new_refresh_token)
    return ApiResponse(code=200, message="刷新token成功", data=token_data) 
from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from typing import List
from app.crud import user as crud
from app.schemas.user import UserSettingCreate, UserSettingUpdate, UserSetting
from app.core.security import get_current_user
from app.schemas.douyin import ApiResponse, DouyinCookieSchema, DouyinCookieResponse
from app.services.douyin import save_douyin_cookie, get_douyin_cookie, DOUYIN_COOKIE_KEY

router = APIRouter()

@router.get("/settings", response_model=ApiResponse[List[UserSetting]], summary="获取用户所有设置")
async def get_user_settings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取当前用户的所有设置项
    """
    settings = crud.get_user_settings(db, current_user.id)
    return ApiResponse(code=200, message="获取成功", data=settings)

@router.get("/settings/{key}", response_model=ApiResponse[UserSetting], summary="获取用户特定设置")
async def get_user_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取当前用户的特定设置项
    """
    setting = crud.get_user_setting(db, current_user.id, key)
    if not setting:
        return ApiResponse(code=404, message="设置项不存在", data=None)
    return ApiResponse(code=200, message="获取成功", data=setting)

@router.post("/settings", response_model=ApiResponse[UserSetting], summary="创建用户设置", status_code=status.HTTP_201_CREATED)
async def create_user_setting(
    setting: UserSettingCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    为当前用户创建新的设置项
    """
    existing_setting = crud.get_user_setting(db, current_user.id, setting.key)
    if existing_setting:
        return ApiResponse(code=400, message="该设置项已存在", data=None)
    
    new_setting = crud.create_user_setting(db, current_user.id, setting)
    return ApiResponse(code=201, message="创建成功", data=new_setting)

@router.put("/settings/{key}", response_model=ApiResponse[UserSetting], summary="更新用户设置")
async def update_user_setting(
    key: str,
    setting: UserSettingUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    更新当前用户的特定设置项
    """
    updated_setting = crud.update_user_setting(db, current_user.id, key, setting)
    if not updated_setting:
        return ApiResponse(code=404, message="设置项不存在", data=None)
    return ApiResponse(code=200, message="更新成功", data=updated_setting)

@router.delete("/settings/{key}", response_model=ApiResponse[dict], summary="删除用户设置")
async def delete_user_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    删除当前用户的特定设置项
    """
    success = crud.delete_user_setting(db, current_user.id, key)
    if not success:
        return ApiResponse(code=404, message="设置项不存在", data=None)
    return ApiResponse(code=200, message="删除成功", data={"key": key})

@router.get("/settings/douyin/cookie", response_model=ApiResponse[DouyinCookieResponse], summary="获取抖音Cookie")
async def get_douyin_cookie_api(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取当前用户保存的抖音Cookie
    """
    cookie = get_douyin_cookie(db, current_user.id)
    if not cookie:
        return ApiResponse(
            code=404, 
            message="未找到抖音Cookie", 
            data=DouyinCookieResponse(success=False, message="未找到抖音Cookie")
        )
    
    return ApiResponse(
        code=200, 
        message="获取成功", 
        data=DouyinCookieResponse(success=True, message=cookie)
    )

@router.post("/settings/douyin/cookie", response_model=ApiResponse[DouyinCookieResponse], summary="设置抖音Cookie")
async def set_douyin_cookie_api(
    cookie_data: DouyinCookieSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    设置当前用户的抖音Cookie
    """
    success = save_douyin_cookie(db, current_user.id, cookie_data.cookie)
    
    if not success:
        return ApiResponse(
            code=500, 
            message="保存Cookie失败", 
            data=DouyinCookieResponse(success=False, message="保存Cookie失败")
        )
    
    return ApiResponse(
        code=200, 
        message="保存成功", 
        data=DouyinCookieResponse(success=True, message="保存成功")
    )
import json
import os
from typing import Optional
from sqlalchemy.orm import Session
from app.crud import user as user_crud
from app.schemas.user import UserSettingCreate, UserSettingUpdate

DOUYIN_COOKIE_KEY = "douyin_cookie"

def save_douyin_cookie(db: Session, user_id: int, cookie: str) -> bool:
    """保存抖音cookie到用户设置"""
    try:
        setting = user_crud.get_user_setting(db, user_id, DOUYIN_COOKIE_KEY)
        if setting:
            updated_setting = user_crud.update_user_setting(
                db, 
                user_id, 
                DOUYIN_COOKIE_KEY, 
                UserSettingUpdate(value=cookie)
            )
            return updated_setting is not None
        else:
            new_setting = user_crud.create_user_setting(
                db,
                user_id,
                UserSettingCreate(
                    key=DOUYIN_COOKIE_KEY,
                    value=cookie,
                    description="抖音Cookie设置"
                )
            )
            return new_setting is not None
    except Exception as e:
        print(f"保存Cookie失败: {e}")
        return False

def get_douyin_cookie(db: Session, user_id: int) -> Optional[str]:
    """从用户设置获取抖音cookie"""
    try:
        setting = user_crud.get_user_setting(db, user_id, DOUYIN_COOKIE_KEY)
        return setting.value if setting else None
    except Exception as e:
        print(f"获取Cookie失败: {e}")
        return None

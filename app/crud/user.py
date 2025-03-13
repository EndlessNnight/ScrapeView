from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List, Optional
from app.models.user import User, UserSetting
from app.schemas.user import UserCreate, UserSettingCreate, UserSettingUpdate
from app.core.security import get_password_hash, verify_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_user_settings(db: Session, user_id: int) -> List[UserSetting]:
    """获取用户的所有设置"""
    return db.query(UserSetting).filter(UserSetting.user_id == user_id).all()

def get_user_setting(db: Session, user_id: int, key: str) -> Optional[UserSetting]:
    """获取用户的特定设置项"""
    return db.query(UserSetting).filter(
        UserSetting.user_id == user_id,
        UserSetting.key == key
    ).first()

def create_user_setting(db: Session, user_id: int, setting: UserSettingCreate) -> UserSetting:
    """创建用户设置项"""
    db_setting = UserSetting(
        user_id=user_id,
        key=setting.key,
        value=setting.value,
        description=setting.description
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def update_user_setting(
    db: Session, user_id: int, key: str, setting: UserSettingUpdate
) -> Optional[UserSetting]:
    """更新用户设置项"""
    db_setting = get_user_setting(db, user_id, key)
    if not db_setting:
        return None
    
    for field, value in setting.model_dump(exclude_unset=True).items():
        setattr(db_setting, field, value)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting

def delete_user_setting(db: Session, user_id: int, key: str) -> bool:
    """删除用户设置项"""
    db_setting = get_user_setting(db, user_id, key)
    if not db_setting:
        return False
    
    db.delete(db_setting)
    db.commit()
    return True 
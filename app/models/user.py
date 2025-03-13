from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    key = Column(String(50), nullable=False, comment="设置项键名")
    value = Column(Text, nullable=True, comment="设置项值")
    description = Column(String(200), nullable=True, comment="设置项描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    # 关联用户
    user = relationship("User", back_populates="settings")

    # 添加联合唯一约束，确保每个用户的每个设置项只有一条记录
    __table_args__ = (
        UniqueConstraint('user_id', 'key', name='uix_user_setting'),
    )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    
    # 关联通知
    notifications = relationship("Notification", back_populates="user")
    # 关联用户设置
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")
    # 关联站点
    sites = relationship("Site", back_populates="user", cascade="all, delete-orphan") 
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.user import User
from app.db.base_class import Base

# 声明式映射
class Site(Base):
    """站点表，保存站点数据"""
    
    __tablename__ = "sites"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="站点名称")
    url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="网址")
    schema_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="架构类型")
    cookie: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Cookie")
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="User-Agent")
    api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="API密钥")
    auth_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="认证令牌")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    # 关联PT用户
    pt_users: Mapped[List["PTUser"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    
    # 关联用户
    user: Mapped["User"] = relationship(back_populates="sites")
    
    # 表选项
    __table_args__ = (
        # 添加唯一约束，确保一个用户只能添加一个特定类型的站点
        UniqueConstraint('user_id', 'schema_type', name='uix_user_schema_type'),
        {"comment": "PT站点表"}
    )
    
    def __repr__(self) -> str:
        return f"<Site(id={self.id}, name={self.name}, url={self.url}, schema_type={self.schema_type})>"


class PTUser(Base):
    """PT用户表，保存PT站点用户数据"""
    
    __tablename__ = "pt_users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    site_id: Mapped[int] = mapped_column(Integer, ForeignKey("sites.id"), nullable=False, comment="所属站点ID")
    username: Mapped[str] = mapped_column(String(100), nullable=False, comment="用户名")
    bonus: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0, comment="魔力值")
    ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0, comment="分享率")
    uploaded: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=0, comment="上传量(GB)")
    downloaded: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=0, comment="下载量(GB)")
    current_upload: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0, comment="当前上传速度(KB/s)")
    current_download: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0, comment="当前下载速度(KB/s)")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 关联站点
    site: Mapped["Site"] = relationship(back_populates="pt_users")
    
    # 表选项
    __table_args__ = {
        "comment": "PT用户表，保存PT站点用户数据"
    }
    
    def __repr__(self) -> str:
        return f"<PTUser(id={self.id}, site_id={self.site_id}, username={self.username})>"


class ProxyImage(Base):
    """代理图片表，保存代理图片数据"""
    
    __tablename__ = "proxy_images"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    original_url: Mapped[str] = mapped_column(String(1024), nullable=False, index=True, comment="原始图片URL")
    local_path: Mapped[str] = mapped_column(String(255), nullable=False, comment="本地存储路径")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="文件名")
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="文件大小(字节)")
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="MIME类型")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 表选项
    __table_args__ = {
        "comment": "代理图片表，保存代理图片数据"
    }
    
    def __repr__(self) -> str:
        return f"<ProxyImage(id={self.id}, original_url={self.original_url}, local_path={self.local_path})>"

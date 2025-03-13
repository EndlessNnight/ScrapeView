from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Float, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class DouyinCreator(Base):
    __tablename__ = "douyin_creators"
    
    id = Column(Integer, primary_key=True, index=True)
    sec_user_id = Column(String(100), unique=True, index=True, nullable=False)
    nickname = Column(String(100), nullable=False)
    avatar_url = Column(Text)
    unique_id = Column(String(100))
    signature = Column(Text)
    ip_location = Column(String(100), nullable=True, comment="IP所在城市")
    gender = Column(Integer, nullable=True, comment="性别")
    follower_count = Column(BigInteger, default=0)
    following_count = Column(BigInteger, nullable=True, comment="关注数")
    aweme_count = Column(BigInteger, nullable=True, comment="作品数")
    total_favorited = Column(BigInteger, default=0)
    status = Column(Integer, default=1)  # 1: 正常, 0: 禁用
    auto_update = Column(Integer, default=1, comment="是否自动更新")
    download_video = Column(Integer, default=1, comment="是否下载视频")
    download_cover = Column(Integer, default=1, comment="是否下载视频封面")
    last_aweme_id = Column(String(50), nullable=True, default="0", comment="最后一条视频ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),  # 首次创建时使用当前时间
        default=func.now(),        # 更新时使用新的时间
        onupdate=func.now(),        # 更新时使用新的时间
        nullable=False
    )
    
    # 关联内容列表
    contents = relationship("DouyinContent", back_populates="creator", cascade="all, delete-orphan")

class DouyinContent(Base):
    """抖音内容信息表（包含视频和图集）"""
    __tablename__ = "douyin_contents"

    id = Column(Integer, primary_key=True, index=True)
    aweme_id = Column(String(50), unique=True, nullable=False, comment="作品ID")
    creator_id = Column(Integer, ForeignKey("douyin_creators.id", ondelete="CASCADE"), nullable=False, comment="创作者ID")
    desc = Column(Text, nullable=True, comment="作品描述")
    group_id = Column(String(50), nullable=True, comment="分组ID")
    create_time = Column(BigInteger, nullable=True, comment="创建时间")
    is_top = Column(Integer, default=0, comment="是否置顶 0：未置顶 1：置顶")
    
    # 内容类型
    content_type = Column(String(20), nullable=False, comment="内容类型: video/image")
    aweme_type = Column(Integer, default=0, comment="抖音类型 0：视频 68：图集")
    media_type = Column(Integer, default=0, comment="媒体类型 2:图片")
    
    # 统计信息
    admire_count = Column(Integer, default=0, comment="点赞数")
    comment_count = Column(Integer, default=0, comment="评论数")
    digg_count = Column(Integer, default=0, comment="点赞数")
    collect_count = Column(Integer, default=0, comment="收藏数")
    play_count = Column(Integer, default=0, comment="播放数")
    share_count = Column(Integer, default=0, comment="分享数")
    
    # 视频特有信息
    duration = Column(Integer, nullable=True, comment="视频时长(毫秒)")
    video_height = Column(Integer, nullable=True, comment="视频高度")
    video_width = Column(Integer, nullable=True, comment="视频宽度")
    
    # 图集特有信息
    images_count = Column(Integer, default=0, comment="图片数量")
    image_urls = Column(JSON, nullable=True, comment="图片URL列表")
    
    # 标签信息，使用JSON存储
    tags = Column(JSON, nullable=True, comment="标签")
    
    # 系统信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="记录更新时间")
    
    # 关联信息
    creator = relationship("DouyinCreator", back_populates="contents")
    files = relationship("DouyinContentFile", back_populates="content", cascade="all, delete-orphan")

class DouyinContentFile(Base):
    """抖音内容文件信息表（包含视频文件和图片文件）"""
    __tablename__ = "douyin_content_files"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("douyin_contents.id", ondelete="CASCADE"), nullable=False, comment="内容ID")
    aweme_id = Column(String(50), index=True, nullable=False, comment="作品ID")
    file_type = Column(String(20), nullable=False, comment="文件类型: video/cover/image")
    
    # 文件索引（对于图集中的图片）
    file_index = Column(Integer, nullable=True, comment="文件索引，用于图集中的图片排序")
    
    # 文件路径
    file_path = Column(String(500), nullable=True, comment="文件路径")
    
    # 封面路径（仅视频类型有）
    cover_path = Column(String(500), nullable=True, comment="封面路径")
    origin_cover_path = Column(String(500), nullable=True, comment="原始封面路径")
    dynamic_cover_path = Column(String(500), nullable=True, comment="动态封面路径")
    
    # 文件信息
    file_size = Column(BigInteger, nullable=True, comment="文件大小(字节)")
    file_hash = Column(String(100), nullable=True, comment="文件哈希值")
    
    # 下载状态
    download_status = Column(String(20), default="pending", comment="下载状态: pending/downloading/completed/failed")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="记录更新时间")
    
    # 关联内容信息
    content = relationship("DouyinContent", back_populates="files")
    
    # 添加联合唯一约束，确保每个内容的每个文件类型和索引只有一条记录
    __table_args__ = (
        UniqueConstraint('aweme_id', 'file_type', 'file_index', name='uix_aweme_id_file_type_index'),
    ) 
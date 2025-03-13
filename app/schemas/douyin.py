from pydantic import BaseModel, Field
from typing import Optional, TypeVar, Generic, Any, List, Dict
from datetime import datetime

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "操作成功"
    data: Optional[T] = None

class PaginationResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int

class DouyinCookieSchema(BaseModel):
    cookie: str
    
class DouyinCookieResponse(BaseModel):
    success: bool
    message: str

# 添加创作者的请求模型
class DouyinCreatorAddRequest(BaseModel):
    share_url: str
    auto_update: int = 1
    download_video: int = 1
    download_cover: int = 1

class DouyinCreatorBase(BaseModel):
    sec_user_id: str
    nickname: str
    avatar_url: Optional[str] = None
    unique_id: Optional[str] = None
    signature: Optional[str] = None
    ip_location: Optional[str] = None
    gender: Optional[int] = None
    follower_count: Optional[int] = 0
    following_count: Optional[int] = None
    aweme_count: Optional[int] = None
    total_favorited: Optional[int] = 0
    status: int = 1
    auto_update: int = 1
    download_video: int = 1
    download_cover: int = 1

class DouyinCreatorCreate(DouyinCreatorBase):
    pass

class DouyinCreatorUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    unique_id: Optional[str] = None
    signature: Optional[str] = None
    ip_location: Optional[str] = None
    gender: Optional[int] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    aweme_count: Optional[int] = None
    total_favorited: Optional[int] = None
    status: Optional[int] = None
    auto_update: Optional[int] = None
    download_video: Optional[int] = None
    download_cover: Optional[int] = None

class DouyinCreatorResponse(DouyinCreatorBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 新的内容文件模型
class DouyinContentFileBase(BaseModel):
    aweme_id: str
    file_type: str  # video/cover/image
    file_index: Optional[int] = None
    file_path: Optional[str] = None
    cover_path: Optional[str] = None
    origin_cover_path: Optional[str] = None
    dynamic_cover_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    download_status: str = "pending"
    error_message: Optional[str] = None

class DouyinContentFileCreate(DouyinContentFileBase):
    content_id: int

class DouyinContentFile(DouyinContentFileBase):
    id: int
    content_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DouyinContentFileUpdate(BaseModel):
    file_path: Optional[str] = None
    cover_path: Optional[str] = None
    origin_cover_path: Optional[str] = None
    dynamic_cover_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    download_status: Optional[str] = None
    error_message: Optional[str] = None

class DouyinContentFileResponse(DouyinContentFileBase):
    id: int
    content_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 新的内容模型（合并视频和图集）
class DouyinContentBase(BaseModel):
    """抖音内容基础模型（包含视频和图集）"""
    aweme_id: str
    creator_id: int
    content_type: str  # video/image
    desc: Optional[str] = None
    group_id: Optional[str] = None
    create_time: Optional[int] = None
    is_top: Optional[int] = 0
    aweme_type: Optional[int] = None
    media_type: Optional[int] = None
    
    # 统计信息
    admire_count: Optional[int] = 0
    comment_count: Optional[int] = 0
    digg_count: Optional[int] = 0
    collect_count: Optional[int] = 0
    play_count: Optional[int] = 0
    share_count: Optional[int] = 0
    
    # 视频特有信息
    duration: Optional[int] = None
    video_height: Optional[int] = None
    video_width: Optional[int] = None
    
    # 图集特有信息
    images_count: Optional[int] = 0
    image_urls: Optional[List[str]] = None
    
    # 标签信息
    tags: Optional[List[Dict[str, Any]]] = None

class DouyinContentCreate(DouyinContentBase):
    pass

class DouyinContent(DouyinContentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DouyinContentUpdate(BaseModel):
    desc: Optional[str] = None
    group_id: Optional[str] = None
    create_time: Optional[int] = None
    is_top: Optional[int] = None
    admire_count: Optional[int] = None
    comment_count: Optional[int] = None
    digg_count: Optional[int] = None
    collect_count: Optional[int] = None
    play_count: Optional[int] = None
    share_count: Optional[int] = None
    duration: Optional[int] = None
    video_height: Optional[int] = None
    video_width: Optional[int] = None
    images_count: Optional[int] = None
    image_urls: Optional[List[str]] = None
    tags: Optional[List[Dict[str, Any]]] = None

class DouyinContentResponse(DouyinContentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    files: Optional[List[DouyinContentFileResponse]] = None

    class Config:
        from_attributes = True

# 新增内容列表响应模型，去掉files信息，增加视频封面和图集图片的相对地址
class DouyinContentListResponse(DouyinContentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 视频封面文件ID
    cover_file_id: Optional[int] = None
    
    # 图集图片文件ID列表
    image_file_ids: Optional[List[int]] = None
    
    class Config:
        from_attributes = True

# 为了向后兼容，保留原来的响应模型名称，但内部使用新的模型
class DouyinVideoResponse(DouyinContentResponse):
    pass

class DouyinImagePostResponse(DouyinContentResponse):
    pass

# 抖音关注用户模型
class DouyinFollowing(BaseModel):
    """抖音关注用户模型"""
    nickname: str
    sec_uid: str
    uid: str
    unique_id: str
    signature: Optional[str] = None
    avatar_thumb: Optional[str] = None
    follow_status: int
    follower_status: int
    custom_verify: Optional[str] = None
    is_creator: bool = False
    creator_id: Optional[int] = None

# 抖音关注列表响应模型
class DouyinFollowingListResponse(BaseModel):
    """抖音关注列表响应模型"""
    followings: List[DouyinFollowing]
    has_more: int
    max_time: int
    min_time: int
    next_req_count: int
    owner_sec_uid: str
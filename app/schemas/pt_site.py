from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Any, Generic, TypeVar
from datetime import datetime
from app.scripts.pt_site.schemas import TorrentInfo
from app.schemas.user import UserResponse
from app.scripts.pt_site.schemas import PTUserInfo


T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """API响应基础模型"""
    code: int
    message: str
    data: Optional[T] = None


class CategoryResponse(BaseModel):
    """分类响应模型"""
    id: int = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")

class PTSitesResponse(BaseModel):
    """PT站点响应模型"""
    # 站点ID
    id: int = Field(..., description="站点ID")
    # 站点名称
    name: str = Field(..., description="站点名称")
    # 架构
    type: str = Field(..., description="站点类型")
    # 类型
    category: List[CategoryResponse] = Field(..., description="站点分类")
    #分享率
    share_rate: float = Field(..., description="分享率")
    # 上传
    upload: str = Field(..., description="上传")
    # 下载
    download: str = Field(..., description="下载")
    # 用户名
    username: str = Field(..., description="用户名")
    # 做种数
    seed: int = Field(..., description="做种数")
    # 时魔
    time_magic: float = Field(..., description="时魔")


class PaginationResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[T]
    total: int

class TorrentListResponse(TorrentInfo):
    """种子列表响应模型"""
    pass

class TorrentDetails(BaseModel):
    """种子详情模型"""
    title: str = Field(..., description="主标题")
    subtitle: str = Field("", description="副标题")
    descr_images: List[str] = Field(default_factory=list, description="简介图片列表")
    peers_info: str = Field("", description="同伴信息")
    info_text: str = Field("", description="基本信息")
    
class TorrentDetailResponse(TorrentDetails):
    """种子详情响应模型"""
    pass 

# 站点模型
class SiteBase(BaseModel):
    """站点基础模型"""
    schema_type: str = Field(..., description="架构类型")
    cookie: Optional[str] = Field(None, description="Cookie")
    user_agent: Optional[str] = Field("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", description="User-Agent")
    api_key: Optional[str] = Field(None, description="API密钥")
    auth_token: Optional[str] = Field(None, description="认证令牌")


class SiteCreate(SiteBase):
    """站点创建模型"""
    pass

class SiteUpdate(BaseModel):
    """站点更新模型"""
    name: Optional[str] = Field(None, description="站点名称")
    cookie: Optional[str] = Field(None, description="Cookie")
    user_agent: Optional[str] = Field(None, description="User-Agent")
    api_key: Optional[str] = Field(None, description="API密钥")
    auth_token: Optional[str] = Field(None, description="认证令牌")



class SiteInDBBase(SiteBase):
    """数据库中的站点模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


    

class PTUserBase(BaseModel):
    """PT用户基础模型"""
    username: str = Field(..., description="用户名")
    bonus: Optional[float] = Field(0, description="魔力值")
    ratio: Optional[float] = Field(0, description="分享率")
    uploaded: Optional[str] = Field("0", description="上传量(GB)")
    downloaded: Optional[str] = Field("0", description="下载量(GB)")
    current_upload: Optional[float] = Field(0, description="当前上传速度(KB/s)")
    current_download: Optional[float] = Field(0, description="当前下载速度(KB/s)")




class PTUserCreate(PTUserBase):
    """PT用户创建模型"""
    pass

class PTUserUpdate(BaseModel):
    """PT用户更新模型"""
    username: Optional[str] = Field(None, description="用户名")
    bonus: Optional[float] = Field(None, description="魔力值")
    ratio: Optional[float] = Field(None, description="分享率")
    uploaded: Optional[str] = Field(None, description="上传量(GB)")
    downloaded: Optional[str] = Field(None, description="下载量(GB)")
    current_upload: Optional[float] = Field(None, description="当前上传速度(KB/s)")
    current_download: Optional[float] = Field(None, description="当前下载速度(KB/s)")

class PTUserResponse(PTUserBase):
    """PT用户响应模型"""
    id: int = Field(..., description="用户ID")
    site_id: int = Field(..., description="站点ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        from_attributes = True

class Site(BaseModel):
    """站点响应模型"""
    id: Optional[int] = Field(None, description="站点ID")
    name: Optional[str] = Field(None, description="站点名称")
    url: Optional[HttpUrl] = Field(None, description="站点URL")
    schema_type: Optional[str] = Field(None, description="架构类型")
    api_key: Optional[str] = Field(None, description="API密钥")
    auth_token: Optional[str] = Field(None, description="认证令牌")
    user_info: Optional[PTUserInfo] = Field(None, description="用户信息")

class SiteWithUsers(Site):
    """包含用户信息的站点模型"""
    pt_users: List[PTUserResponse] = []
    user: Optional[UserResponse] = None

class SupportedSite(BaseModel):
    """支持的站点模型"""
    name: str = Field(..., description="站点名称")
    type: str = Field(..., description="站点类型")


class ProxyImageBase(BaseModel):
    """代理图片基础模型"""
    original_url: str = Field(..., description="原始图片URL")
    headers: Optional[dict] = Field(None, description="自定义请求头")


class ProxyImageCreate(ProxyImageBase):
    """创建代理图片模型"""
    pass


class ProxyImageUpdate(BaseModel):
    """更新代理图片模型"""
    original_url: Optional[str] = Field(None, description="原始图片URL")
    local_path: Optional[str] = Field(None, description="本地存储路径")
    file_name: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    mime_type: Optional[str] = Field(None, description="MIME类型")


class ProxyImageResponse(ProxyImageBase):
    """代理图片响应模型"""
    id: int = Field(..., description="图片ID")
    local_path: str = Field(..., description="本地存储路径")
    file_name: str = Field(..., description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True
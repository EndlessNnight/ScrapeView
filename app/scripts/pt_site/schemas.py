from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TorrentInfo(BaseModel):
    """种子基本信息"""
    torrent_id: int
    title: str
    subtitle: Optional[str] = None
    cover_url: Optional[str] = None
    tags: List[str] = []
    discount: Optional[str] = None
    free_until: Optional[datetime] = None
    size: str
    seeders: int
    leechers: int
    up_time: Optional[datetime] = None
    finished: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "torrent_id": 1,
                "title": "The Best Thing 2025 S01 E17-E18 2160p IQ WEB-DL H265 DDP5.1-PTerWEB",
                "subtitle": "爱你/爱上你是我做过最好的事 第17-18集 | 导演: 车亮逸 主演: 张凌赫 徐若晗 王宥钧 [国语/中字]",
                "cover_url": "https://img9.doubanio.com/view/photo/l_ratio_poster/public/p2918882215.jpg",
                "tags": ["官方", "国语", "中字"],
                "discount": "免费",
                "free_until": "2025-03-06T07:43:28",
                "size": "2.42GB",
                "seeders": 1,
                "leechers": 45,
                "up_time": "2025-03-06T07:43:28",
                "finished": 1
            }
        }

class TorrentInfoList(BaseModel):
    """种子列表"""
    torrents: List[TorrentInfo] = []

class TorrentDetails(BaseModel):
    """种子详细信息"""
    title: str = ""
    subtitle: str = ""
    descr_images: List[str] = []
    peers_info: str = ""
    info_text: str = ""
    seeders: Optional[int] = None
    leechers: Optional[int] = None
    discount: Optional[str] = None
    free_until: Optional[datetime] = None
    torrent_name: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Mouth 2018 S01 Complete LiTV WEB-DL 1080p x264 AAC 2.0-CMCTV    [免费] 剩余时间：16时43分",
                "subtitle": "口之法则 / 嘴（台） | 全18集 | 主演: 阿萍雅·萨库尔加伦苏 泽纶娅·秀利隆坤泽坤 友塔纳·布格朗 [泰语/繁中]",
                "descr_images": ['https://cache.springsunday.net/img9.doubanio.com/view/photo/l_ratio_poster/public/p2532985155.jpg', 'https://static.hdcmct.org/cmct-images/2024/01/14/UoMvF.jpg'],
                "peers_info": "1个做种者 | 19个下载者",
                "info_text": "导演: 车亮逸 主演: 张凌赫 徐若晗 王宥钧 [国语/中字]",
                "seeders": 1,
                "leechers": 19,
                "discount": "免费",
                "free_until": "2025-03-06T07:43:28"
            }
        }

class PTUserInfo(BaseModel):
    """PT用户信息"""
    username: str
    bonus: float
    ratio: float
    uploaded: str
    downloaded: str
    seeding: int
    leeching: int

class SiteConfig(BaseModel):
    """站点配置"""
    site_name: str
    base_url: str
    login_url: Optional[str] = None
    torrents_url: str
    details_url: str
    search_url: str
    user_info_url: str
    user_info_peer_url: Optional[str] = None
    default_categories: List[int] = []
    site_type: str = "NexusPHP"  # 站点类型，如 NexusPHP, Gazelle 等
    encoding: str = "utf-8"
    timeout: int = 30
    
    class Config:
        arbitrary_types_allowed = True

class PTUserInfo(BaseModel):
    """PT用户信息"""
    username: str
    bonus: float
    ratio: float
    uploaded: str
    downloaded: str
    seeding: int
    leeching: int

class Category(BaseModel):
    """分类"""
    id: int = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")

class CategoryDetail(BaseModel):
    """分类详情"""
    id: int = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    params: Optional[str] = Field(None, description="分类参数")


class ParseTableTitle(BaseModel):
    """解析表头"""
    torrent_id: str = Field(..., description="种子ID")
    title: str = Field(..., description="标题")
    subtitle: Optional[str] = Field(None, description="副标题")
    tags: Optional[List[str]] = Field([], description="标签")
    discount: Optional[str] = Field(None, description="折扣")
    free_until: Optional[str] = Field(None, description="免费剩余时间")
    cover_url: Optional[str] = Field(None, description="封面URL")
    

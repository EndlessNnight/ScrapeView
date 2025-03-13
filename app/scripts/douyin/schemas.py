from pydantic import BaseModel, field_validator, Field
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import json

class Url(BaseModel):
    url: str


class BaseRequestModel(BaseModel):
    device_platform: str = "webapp"
    aid: str = "6383"
    channel: str = "channel_pc_web"
    pc_client_type: int = 1
    version_code: str = "190500"
    version_name: str = "19.5.0"
    cookie_enabled: str = "true"
    screen_width: int = 1920
    screen_height: int = 1080
    browser_language: str = "zh-CN"
    browser_platform: str = "Win32"
    browser_name: str = "Firefox"
    browser_version: str = "124.0"
    browser_online: str = "true"
    engine_name: str = "Gecko"
    engine_version: str = "122.0.0.0"
    os_name: str = "Windows"
    os_version: str = "10"
    cpu_core_num: int = 12
    device_memory: int = 8
    platform: str = "PC"
    msToken: str = ""


class PostCommentsReply(BaseRequestModel):
    item_id: str
    comment_id: str
    cursor: int = 0
    count: int = 20
    item_type: int = 0


class Profile(BaseRequestModel):
    sec_user_id: str

class UserShortInfo(BaseRequestModel):
    sec_user_id: Optional[str] = None

class FollowingList(BaseRequestModel):
    count: int = 50
    source: str = "source"
    need_remove_share_panel: str = "true"
    need_sorted_info: str = "true"
    with_fstatus: int = 1
    max_time: int = 0
    min_time: int = 0

class Following(BaseRequestModel):
    sec_user_id: str
    user_id: str
    min_time: int = 0
    max_time: int = 0
    count: int = 20
    source_type: int = 4
    offset: int = 0


class HotList(BaseRequestModel):
    detail_list: int = 1
    source: int = 6
    board_type: int = 0  # 0：为总榜  board_sub_type 为空 2: 指定 board_sub_type 参数获取单独榜单
    board_sub_type: int | None = None  # 榜单切换，2：娱乐榜 4：社会榜 hotspot_challenge：挑战榜


class CreatorVideoList(BaseRequestModel):
    sec_user_id: str
    max_cursor: int = 0  # 最大游标
    count: int = 20  # 数量

class FetchOneVideo(BaseRequestModel):
    aweme_id: str

class UserInfoBase(BaseModel):
    id: int
    uid: str
    unique_id: str
    sec_uid: str
    share_url: str
    nickname: str
    new_nickname: str
    watch_status: int
    aweme_count: int
    follower_count: int
    following_count: int
    city: str
    signature: str
    up_time: int
    create_time: int
    save_path: str


class CreatorBase(BaseModel):
    # id: int
    uid: Optional[str] = None
    unique_id: str
    sec_user_id: str
    nickname: str
    avatar: str
    gender: Optional[int] = None
    update_time: Optional[Union[str, datetime]]
    create_time: Optional[Union[str, datetime]]
    desc: str
    follows: int
    fans: str
    interaction: str
    videos_count: str
    is_update: int
    is_download: int
    status: int | None = None
    content: str | None = None
    title: str | None = None
    ip_location: str | None = None
    class Config:
        from_attributes = True

    @field_validator('update_time', 'create_time', mode='before')
    def convert_to_string(cls, value):
        if isinstance(value, datetime):
            return value.isoformat(sep=" ", timespec="seconds")
            # return value.strftime('%Y-%m-%d %H:%M:%S')  # 转换为字符串格式
        return value


class CreatorChangeInfoBase(BaseModel):
    data: Optional[Union[int, str]]
    add_time: Optional[Union[str, datetime]]

    class Config:
        from_attributes = True

    @field_validator('add_time', mode='before')
    def convert_to_string(cls, value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')  # 转换为字符串格式
        return value


    @field_validator('data', mode='before')
    def string_to_int(cls, value):
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return value
        return value
    
    
class VideoDownloadBase(BaseModel):
    sec_user_id: str
    aweme_id: str
    is_download_cover: int
    save_path: str
    update_time:Optional[Union[str, datetime]]
    create_time: Optional[Union[str, datetime]]
    
    @field_validator('update_time','create_time', mode='before')
    def convert_to_string(cls, value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')  # 转换为字符串格式
        return value
    
    class Config:
        from_attributes = True
        
class DBUserVideoOut(BaseModel):
    aweme_id: str
    desc: str
    group_id: str 
    is_top: int
    comment_gid: str
    comment_count: str
    digg_count: int
    collect_count: int
    share_count: int
    create_time: int
    source_play: Optional[str | dict | list]
    source_cover: Optional[str | dict | list]
    # local_play: Optional[str | None] = None
    # local_cover: Optional[str | None] = None
    media_type: int
    aweme_type: int
    duration: int
    is_download: int
    is_cretor_delete: int
    class Config:
        from_attributes = True
        
    @field_validator('source_play','source_cover', 'is_download', mode='before')
    def convert_to_string(cls, value):
        if isinstance(value, str):
            return json.loads(value)
        return value

class DownloadTaskResult(BaseModel):
    """下载任务结果"""
    success: bool = Field(default=False, description="是否下载成功")
    file_path: str = Field(default="", description="文件保存路径")
    file_size: int = Field(default=0, description="文件大小(字节)")
    file_hash: str = Field(default="", description="文件MD5哈希值")
    error: str = Field(default="", description="错误信息")
    cover_type: Optional[str] = Field(default=None, description="封面类型(仅封面文件有此字段)")
    image_index: Optional[int] = Field(default=None, description="图片序号(仅图集图片有此字段)")

class DownloadResult(BaseModel):
    """单个视频的下载结果"""
    aweme_id: str = Field(..., description="视频ID")
    video: DownloadTaskResult = Field(default_factory=DownloadTaskResult, description="视频下载结果")
    cover: DownloadTaskResult = Field(default_factory=DownloadTaskResult, description="封面下载结果")
    origin_cover: DownloadTaskResult = Field(default_factory=DownloadTaskResult, description="原始封面下载结果")
    dynamic_cover: DownloadTaskResult = Field(default_factory=DownloadTaskResult, description="动态封面下载结果")
    images: List[DownloadTaskResult] = Field(default_factory=list, description="图片下载结果列表")

class CoverUrls(BaseModel):
    """封面URL信息"""
    cover_type: str = Field(..., description="封面类型")
    url: List[str] = Field(..., description="URL列表")

class DownloadTask(BaseModel):
    """下载任务"""
    sec_user_id: str = Field(..., description="创作者ID")
    aweme_id: str = Field(..., description="视频ID")
    image_urls: List[str] = Field(default_factory=list, description="图片下载地址列表")
    video_urls: List[str] = Field(default_factory=list, description="视频下载地址列表")
    cover_urls: List[CoverUrls] = Field(default_factory=list, description="封面下载地址列表")
    content_id: Optional[int] = Field(default=None, description="内容ID，用于关联DouyinContent记录")

    class Config:
        json_schema_extra = {
            "example": {
                "sec_user_id": "MS4wLjABAAAAEyc7f8rfVXdpGZSd833RILo2zry0cEmYx5M7xXIW_U4-07BtwncUJsK3wiNrSt4a",
                "aweme_id": "7425582833831316773",
                "video_urls": ["https://www.example.com/video.mp4"],
                "cover_urls": [
                    {
                        "cover_type": "cover",
                        "url": ["https://www.example.com/cover.jpg"]
                    }
                ],
                "content_id": 123
            }
        }

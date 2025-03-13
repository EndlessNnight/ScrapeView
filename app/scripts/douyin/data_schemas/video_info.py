from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

class Statistics(BaseModel):
    admire_count: Optional[int] = 0  #
    comment_count: Optional[int] = 0  # 评论数
    digg_count: Optional[int] = 0  # 点赞数量
    collect_count: Optional[int] = 0  # 收藏
    play_count: Optional[int] = 0  # 播放数量 获取不到
    share_count: Optional[int] = 0  # 分享数量


class UrlAddr(BaseModel):
    uri: Optional[str] = ""
    url_list: Optional[list[str]] = []
    download_url_list: Optional[list[str]] = []  # 有水印
    height: Optional[int] = 0
    width: Optional[int] = 0
    data_size: Optional[int] = 0
    file_hash: Optional[str] = ""


class Video(BaseModel):
    play_addr: Optional[UrlAddr] = None
    cover: Optional[UrlAddr] = None
    origin_cover: Optional[UrlAddr] = None  # 源封面
    statistics: Optional[Statistics] = None
    dynamic_cover: Optional[UrlAddr] = None  # 动态封面？
    duration: Optional[int] = 0  # 持续时间 毫秒


class VideoTag(BaseModel):
    tag_id: Optional[int] = 0
    level: Optional[int] = 0
    tag_name: Optional[str] = ""


class Author(BaseModel):
    sec_uid: Optional[str] = ""
    uid: Optional[str] = ""
    nickname: Optional[str] = ""
    signature: Optional[str] = None
    following_count: Optional[int] = None
    follower_count: Optional[int] = None
    total_favorited: Optional[int] = None
    unique_id: Optional[str] = None

class AwemeList(BaseModel):
    aweme_id: Optional[str] = ""
    desc: Optional[str] = ""
    group_id: Optional[str] = ""  # 分组ID

    create_time: Optional[int] = 0
    is_top: Optional[int] = 0  # 是否置顶 0：未置顶 1：置顶
    aweme_type: Optional[int] = 0  # 0：视频 1 or 68：图集
    media_type: Optional[int] = 0  # 媒体类型 2:图片
    comment_gid: Optional[int] = 0  # 评论回复id

    statistics: Optional[Statistics] = Statistics()
    video_tag: Optional[list[VideoTag]] = None
    video: Optional[Video] = None
    images: Optional[list[UrlAddr]] = None
    author: Optional[Author] = None


class Base(BaseModel):
    status_code: Optional[int] = 0
    min_cursor: Optional[int] = 0
    max_cursor: Optional[int] = 0
    has_more: Optional[int] = 0
    aweme_list: Optional[list[AwemeList]] = []
    post_serial: Optional[int] = 0
    request_item_cursor: Optional[int] = 0
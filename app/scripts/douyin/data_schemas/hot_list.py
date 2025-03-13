from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class WordCover(BaseModel):
    uri: str
    url_list: List[str]


class TrendingListItem(BaseModel):
    article_detail_count: int = None
    aweme_infos: Any = None
    discuss_video_count: int = None
    display_style: int = None
    drift_info: Any = None
    event_time: int = None
    group_id: str = None
    hot_value: int = None
    hotlist_param: str = None
    label: int = None
    related_words: Any = None
    sentence_id: str = None
    sentence_tag: int = None
    video_count: int = None
    word: str = None
    word_cover: WordCover = None
    word_sub_board: Any = None
    word_type: int = None


class WordCover1(BaseModel):
    uri: str
    url_list: List[str]


class WordListItem(BaseModel):
    aweme_infos: Any = None
    can_extend_detail: bool = None
    discuss_video_count: int = None
    drift_info: Any = None
    hot_value: int = None  # 热度
    hotlist_param: str = None
    label: int = None  # 标签 0：无标签 1：新 3:热  5：首发 8：独家 16：辟谣
    related_words: Any = None
    sentence_id: str = None    # 查询视频用到
    topic_info: Optional[Dict[str, Any]] = None
    view_count: int = None  # 浏览量
    word: str = None  # 热词
    word_sub_board: Any = None
    word_type: int  # 热词类型 word_type=1 热词 word_type=14 置顶
    article_detail_count: Optional[int] = None
    display_style: Optional[int] = None
    event_time: Optional[int] = None   # 上榜时间？
    group_id: Optional[str] = None
    position: Optional[int] = None
    sentence_tag: Optional[int] = None
    video_count: Optional[int] = None   # 视频数量
    word_cover: Optional[WordCover1] = None


class Data(BaseModel):
    active_time: str = None
    recommend_list: Any = None
    trending_desc: str = None
    trending_list: List[TrendingListItem] = None
    word_list: List[WordListItem]


class Base(BaseModel):
    data: Optional[Data] = None
    status_code: Optional[int] = None

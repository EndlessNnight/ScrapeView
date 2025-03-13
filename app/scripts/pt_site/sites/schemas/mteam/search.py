from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Status(BaseModel):
    id: Optional[str]
    created_date: Optional[str] = Field(..., alias='createdDate')
    last_modified_date: Optional[str] = Field(..., alias='lastModifiedDate')
    pick_type: Optional[str] = Field(..., alias='pickType')
    topping_level: Optional[str] = Field(..., alias='toppingLevel')
    topping_end_time: Optional[str] = Field(..., alias='toppingEndTime')
    discount: Optional[str]
    discount_end_time: Optional[Optional[str]] = Field(..., alias='discountEndTime')
    times_completed: Optional[str] = Field(..., alias='timesCompleted')
    comments: Optional[str]
    last_action: Optional[str] = Field(..., alias='lastAction')
    last_seeder_action: Optional[str] = Field(..., alias='lastSeederAction')
    views: Optional[str]
    hits: Optional[str]
    support: Optional[str]
    oppose: Optional[str]
    status: Optional[str]
    seeders: Optional[str]
    leechers: Optional[str]
    banned: Optional[bool]
    visible: Optional[bool]
    promotion_rule: Any = Field(..., alias='promotionRule')
    mall_single_free: Any = Field(..., alias='mallSingleFree')


class Datum(BaseModel):
    id: Optional[str]
    created_date: Optional[str] = Field(..., alias='createdDate')
    last_modified_date: Optional[str] = Field(..., alias='lastModifiedDate')
    name: Optional[str]
    small_descr: Optional[str] = Field(..., alias='smallDescr')
    imdb: Optional[str]
    imdb_rating: Optional[Optional[str]] = Field(..., alias='imdbRating')
    douban: Optional[str]
    douban_rating: Optional[str] = Field(..., alias='doubanRating')
    dmm_code: Any = Field(..., alias='dmmCode')
    author: Any
    category: Optional[str]
    source: Optional[str]
    medium: Any
    standard: Optional[str]
    video_codec: Optional[str] = Field(..., alias='videoCodec')
    audio_codec: Optional[str] = Field(..., alias='audioCodec')
    team: Optional[str]
    processing: Any
    countries: List[Optional[str]]
    numfiles: Optional[str]
    size: Optional[str]
    tags: Optional[str]
    labels: Optional[str]
    ms_up: Optional[str] = Field(..., alias='msUp')
    anonymous: Optional[bool]
    info_hash: Any = Field(..., alias='infoHash')
    status: Status
    edited_by: Any = Field(..., alias='editedBy')
    edit_date: Optional[str] = Field(..., alias='editDate')
    collection: Optional[bool]
    in_rss: Optional[bool] = Field(..., alias='inRss')
    can_vote: Optional[bool] = Field(..., alias='canVote')
    image_list: List[str] = Field(..., alias='imageList')
    reset_box: Any = Field(..., alias='resetBox')


class Data(BaseModel):
    page_number: str = Field(..., alias='pageNumber')
    page_size: str = Field(..., alias='pageSize')
    total: str
    total_pages: str = Field(..., alias='totalPages')
    data: List[Datum]


class ResponseModel(BaseModel):
    message: Optional[str] = None
    data: Optional[Data] = None
    code: Optional[str | int] = None



class RequestSearch(BaseModel):
    """搜索响应"""
    categories: List[str] = Field(default=[], alias='categories')
    mode: str = Field(default="movie", alias='mode') # 搜索模式 movie
    pageNumber: int = Field(default=1, alias='pageNumber')
    pageSize: int = Field(default=100, alias='pageSize')
    visible: Optional[int] = Field(default=1, alias='visible') # 可见性 0 全部 1 可见 2 不可见
    keyword: Optional[str] = Field(default=None, alias='keyword') # 搜索关键词


class RequestModel(BaseModel):
    search: RequestSearch
    

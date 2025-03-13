from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Status(BaseModel):
    id: Optional[str]
    created_date: Optional[str] = Field(..., alias='createdDate')
    last_modified_date: Optional[str] = Field(..., alias='lastModifiedDate')
    pick_type: Optional[str] = Field(..., alias='pickType')
    topping_level: Optional[str] = Field(..., alias='toppingLevel')
    topping_end_time: Any = Field(..., alias='toppingEndTime')
    discount: Optional[str]
    discount_end_time: Any = Field(..., alias='discountEndTime')
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
    banned: bool
    visible: bool
    promotion_rule: Any = Field(..., alias='promotionRule')
    mall_single_free: Any = Field(..., alias='mallSingleFree')


class Data(BaseModel):
    id: Optional[str]
    created_date: Optional[str] = Field(..., alias='createdDate')
    last_modified_date: Optional[str] = Field(..., alias='lastModifiedDate')
    name: Optional[str]
    small_descr: Optional[str] = Field(..., alias='smallDescr')
    imdb: Optional[str]
    imdb_rating: Any = Field(..., alias='imdbRating')
    douban: Optional[str]
    douban_rating: Any = Field(..., alias='doubanRating')
    dmm_code: Optional[str] = Field(..., alias='dmmCode')
    author: Any
    category: Optional[str]
    source: Optional[str]
    medium: Any
    standard: Optional[str]
    video_codec: Optional[str] = Field(..., alias='videoCodec')
    audio_codec: Optional[str] = Field(..., alias='audioCodec')
    team: Any
    processing: Any
    countries: List
    numfiles: Optional[str]
    size: Optional[str]
    tags: Optional[str]
    labels: Optional[str]
    ms_up: Optional[str] = Field(..., alias='msUp')
    anonymous: bool
    info_hash: Any = Field(..., alias='infoHash')
    status: Status
    edited_by: Any = Field(..., alias='editedBy')
    edit_date: Optional[str] = Field(..., alias='editDate')
    collection: bool
    in_rss: bool = Field(..., alias='inRss')
    can_vote: bool = Field(..., alias='canVote')
    image_list: List[str] = Field(..., alias='imageList')
    reset_box: Any = Field(..., alias='resetBox')
    origin_file_name: str = Field(..., alias='originFileName')
    descr: Optional[str]
    nfo: Any
    mediainfo: Optional[str]
    cids: Any
    aids: Any
    showcase_list: List = Field(..., alias='showcaseList')
    tag_list: List = Field(..., alias='tagList')
    scope: Optional[str]
    scope_teams: Any = Field(..., alias='scopeTeams')
    thanked: bool
    rewarded: bool


class ResponseModel(BaseModel):
    message: Optional[str] = None
    data: Optional[Data] = None
    code: Optional[str] = None

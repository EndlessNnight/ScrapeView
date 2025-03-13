from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ValidationError, Field, field_validator

import json


class GetSecUserIdModel(BaseModel):
    code: Optional[int] = None
    router: Optional[str] = None
    data: Optional[str] = None


class AvatarLarger(BaseModel):
    height: int
    uri: str
    url_list: List[str]
    width: int


class SpecialStateInfo(BaseModel):
    content: str = None
    special_state: int = 0
    title: str = None

class Owner(BaseModel):
    web_rid: str    #  直播间ID


class FlvPullUrl(BaseModel):
    full_hd1: str = Field(..., alias='FULL_HD1')
    hd1: str = Field(..., alias='HD1')
    sd1: str = Field(..., alias='SD1')
    sd2: str = Field(..., alias='SD2')
    
class Extra(BaseModel):
    height: int
    width: int

class Play(BaseModel):
    horizontal: str
    vertical: str
class StreamUrl(BaseModel):
    default_resolution: str
    # extra: Extra
    flv_pull_url: FlvPullUrl
    stream_orientation: int
    # play: Play

class RoomData(BaseModel):
    status: Optional[int] = None
    user_count: Optional[int] = None
    stream_url: Optional[StreamUrl] = None
    owner: Optional[Owner] = None
    live_type_normal: Optional[bool] = None
    # paid_live_data: Optional[PaidLiveData] = None
    # ecom_data: Optional[EcomData] = None
    # pack_meta: Optional[PackMeta] = None
    # others: Optional[Others] = None

class User(BaseModel):
    sec_uid: Optional[str] = None
    uid: Optional[str] = None
    avatar_larger: Optional[AvatarLarger] = None
    ip_location: Optional[str] = None
    signature: Optional[str] = None
    gender: Optional[int] = None
    following_count: Optional[int] = None
    follower_count: Optional[int] = None
    total_favorited: Optional[int] = None
    aweme_count: Optional[int] = None
    unique_id: Optional[str] = None
    nickname: Optional[str] = None
    user_deleted: Optional[bool] = None
    special_state_info: Optional[SpecialStateInfo] = None
    live_status: Optional[int] = None
    room_data: Optional[RoomData] = None
    room_id: Optional[int] = None
    room_id_str: Optional[str] = None
    
    @field_validator('room_data', mode='before')
    def parse_json_data(cls, value):
        if isinstance(value, str):
            try:
                data_dict = json.loads(value)
                return RoomData(**data_dict)
            except (json.JSONDecodeError, TypeError, ValidationError) as e:
                return None
        elif value is None:
            return None
        elif isinstance(value, dict):
            return RoomData(**value)
        else:
            return None

class Base(BaseModel):
    status_code: int
    status_msg: Any
    user: User

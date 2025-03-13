from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AvatarSmall(BaseModel):
    uri: str
    url_list: List[str]


class AvatarThumb(BaseModel):
    uri: str
    url_list: List[str]


class Following(BaseModel):
    account_cert_info: str
    avatar_signature: str
    avatar_small: AvatarSmall
    avatar_thumb: AvatarThumb
    commerce_user_level: int
    custom_verify: str
    enterprise_verify_reason: str
    follow_status: int
    follower_status: int
    has_e_account_role: bool
    im_activeness: int
    im_role_ids: List
    nickname: str
    sec_uid: str
    short_id: str
    signature: str
    social_relation_sub_type: int
    social_relation_type: int
    uid: str
    unique_id: str
    verification_type: int
    webcast_sp_info: Dict[str, Any]


class Base(BaseModel):
    abnormal_sorted: Optional[int] = None
    followings: Optional[List[Following]] = None
    has_more: Optional[int] = None
    max_time: Optional[int] = None
    min_time: Optional[int] = None
    next_req_count: Optional[int] = None
    owner_sec_uid: Optional[str] = None
    status_code: Optional[int] = None

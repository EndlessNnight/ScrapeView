from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Extra(BaseModel):
    fatal_item_ids: List
    logid: str
    now: int


class LogPb(BaseModel):
    impr_id: str


class Following(BaseModel):
    nickname: str
    sec_uid: str
    signature: str
    uid: str
    unique_id: str
    unique_id_modify_time: int


class Base(BaseModel):
    extra: Optional[Extra] = None
    followings: Optional[List[Following]] = None
    has_more: Optional[bool] = None
    hotsoon_has_more: Optional[int] = None
    hotsoon_text: Optional[str] = None
    log_pb: Optional[LogPb] = None
    max_time: Optional[int] = None
    min_time: Optional[int] = None
    mix_count: Optional[int] = None
    myself_user_id: Optional[str] = None
    offset: Optional[int] = None
    rec_has_more: Optional[bool] = None
    status_code: Optional[int] = None
    store_page: Optional[str] = None
    total: Optional[int] = None
    vcd_count: Optional[int] = None

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.scripts.douyin.data_schemas.video_info import AwemeList

class FilterDetail(BaseModel):
    aweme_id: Optional[str] = None
    detail_msg: Optional[str] = None
    filter_reason: Optional[str] = None
    icon: Optional[str] = None
    notice: Optional[str] = None

class Base(BaseModel):
    status_code: Optional[int] = 0
    aweme_detail: Optional[AwemeList] = AwemeList()
    filter_detail: Optional[FilterDetail] = None

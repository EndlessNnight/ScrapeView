from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Type(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class Peers(BaseModel):
    upload: Optional[int] = None
    download:  Optional[int] = None


class SnatchInfo(BaseModel):
    status: Optional[str] = None # SEED STOP
    progress: Optional[int] = None # 0-100

class Status(BaseModel):
    tid: Optional[int] = None
    startAt: Optional[int] = None
    endAt: Optional[int] = None
    name: Optional[str] = None
    class_: str = Field(..., alias='class')
    upCoefficient: Optional[int] = None
    downCoefficient: Optional[int] = None


class ListItem(BaseModel):
    tid: Optional[int] = None
    title: Optional[str] = None
    type: Optional[Type] = None
    cover: Optional[str] = None
    fileRawSize: Optional[int] = None
    fileSize: Optional[str] = None
    fileHash: Optional[str] = None
    createdTs: Optional[int] = None
    finish: Optional[int] = None
    isTop: Optional[str] = None
    tags: Optional[List[str]] = None
    actress: Optional[List] = None
    peers: Optional[Peers] = None
    status: Optional[Status] = None
    favoriteStatus: Optional[str] = None
    snatchInfo: Optional[SnatchInfo] = None

class Data(BaseModel):
    maxPage: Optional[int] = None
    torrentCount: Optional[int] = None
    list: List[ListItem]


class ResponseModel(BaseModel):
    success: Optional[bool] = None
    msg: Optional[str] = None
    data: Optional[Data] = None


class RequestModel(BaseModel):
    type: int = Field(default=0, alias='type')
    systematics: int = Field(default=0, alias='systematics')
    tags: List[int] = Field(default=[], alias='tags')
    page: int = Field(default=1, alias='page')
    keyword: Optional[str] = Field(default=None, alias='keyword')



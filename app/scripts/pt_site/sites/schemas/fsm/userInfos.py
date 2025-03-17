from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class UserRank(BaseModel):
    id: int
    raw: str
    name: str
    vote_rank: int = Field(..., alias='voteRank')
    class_: str = Field(..., alias='class')
    is_admin: str = Field(..., alias='isAdmin')


class Peers(BaseModel):
    upload: int
    download: int


class Free(BaseModel):
    has_free: bool = Field(..., alias='hasFree')


class Data(BaseModel):
    uid: int
    username: str
    user_rank: UserRank = Field(..., alias='userRank')
    point: int
    profile: str
    upload: str
    download: str
    avatar: str
    seed_gh: float = Field(..., alias='seedGH')
    buffer: int
    passkey: str
    badges: List
    peers: Peers
    free: Free


class ResponseModel(BaseModel):
    success: Optional[bool] = None
    msg: Optional[str] = None
    data: Optional[Data] = None

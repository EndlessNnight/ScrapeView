from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Type(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class Status(BaseModel):
    tid: Optional[int] = None
    start_at: Optional[int] = Field(None, alias='startAt')
    end_at: Optional[int] = Field(None, alias='endAt')
    name: Optional[str] = None
    class_: Optional[str] = Field(None, alias='class')
    up_coefficient: Optional[int] = Field(None, alias='upCoefficient')
    down_coefficient: Optional[int] = Field(None, alias='downCoefficient')


class Peers(BaseModel):
    upload: Optional[str|int] = None
    download: Optional[str|int] = None


class Torrent(BaseModel):
    tid: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[Type] = None
    cover: Optional[str] = None
    file_raw_size: Optional[int] = Field(None, alias='fileRawSize')
    file_size: Optional[str] = Field(None, alias='fileSize')
    file_path: Optional[str] = Field(None, alias='filePath')
    file_hash: Optional[str] = Field(None, alias='fileHash')
    created_ts: Optional[int] = Field(None, alias='createdTs')
    reply_num: Optional[int] = Field(None, alias='replyNum')
    get_point: Optional[int] = Field(None, alias='getPoint')
    finish: Optional[int] = None
    is_top: Optional[str] = Field(None, alias='isTop')
    is_del: Optional[str] = Field(None, alias='isDel')
    tags: Optional[List[str]] = None
    actress: Optional[List] = None
    screenshots: Optional[List] = None
    status: Optional[Status] = None
    peers: Optional[Peers] = None
    vote_status: Optional[str] = Field(None, alias='voteStatus')
    is_owner: Optional[bool] = Field(None, alias='isOwner')
    can_edit: Optional[bool] = Field(None, alias='canEdit')


class UserRank(BaseModel):
    id: Optional[int] = None    
    raw: Optional[str] = None   
    name: Optional[str] = None
    vote_rank: Optional[int] = Field(None, alias='voteRank')
    class_: Optional[str] = Field(None, alias='class')
    is_admin: Optional[str] = Field(None, alias='isAdmin')


class UserInfo(BaseModel):
    uid: Optional[int] = None
    username: Optional[str] = None
    user_rank: Optional[UserRank] = Field(None, alias='userRank')
    point: Optional[int] = None
    profile: Optional[str] = None
    upload: Optional[str] = None
    download: Optional[str] = None
    avatar: Optional[str] = None
    seed_gh: Optional[float] = Field(None, alias='seedGH')
    buffer: Optional[int] = None
    badges: Optional[List] = None


class ListItem(BaseModel):
    id: Optional[int] = None
    uid: Optional[int] = None
    tid: Optional[int] = None
    comment: Optional[str] = None
    is_del: Optional[str] = Field(None, alias='isDel')
    ts: Optional[int] = None
    user_info: Optional[UserInfo] = Field(None, alias='userInfo')
    is_owner: Optional[bool] = Field(None, alias='isOwner')


class CommentInfo(BaseModel):
    max_page: Optional[int] = Field(None, alias='maxPage')
    has_comment: Optional[bool] = Field(None, alias='hasComment')
    list: Optional[List[ListItem]] = None


class Data(BaseModel):
    torrent: Optional[Torrent] = None
    comment_info: Optional[CommentInfo] = Field(None, alias='commentInfo')


class ResponseModel(BaseModel):
    success: Optional[bool] = None
    msg: Optional[str] = None
    data: Optional[Data] = None


class RequestModel(BaseModel):
    tid: Optional[int] = None
    page: Optional[int] = None


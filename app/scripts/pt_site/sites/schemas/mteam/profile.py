from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class MemberStatus(BaseModel):
    created_date: Optional[str] = Field(..., alias='createdDate')
    last_modified_date: Optional[str] = Field(..., alias='lastModifiedDate')
    id: Optional[str]
    vip: Optional[bool]
    vip_until: Any = Field(..., alias='vipUntil')
    vip_added: Any = Field(..., alias='vipAdded')
    vip_duties: Optional[str] = Field(..., alias='vipDuties')
    donor: Optional[bool]
    donor_until: Any = Field(..., alias='donorUntil')
    noad: Optional[bool]
    noad_until: Any = Field(..., alias='noadUntil')
    warned: Optional[bool]
    warned_until: Any = Field(..., alias='warnedUntil')
    leech_warn: Optional[bool] = Field(..., alias='leechWarn')
    leech_warn_until: Any = Field(..., alias='leechWarnUntil')
    last_login: Optional[str] = Field(..., alias='lastLogin')
    last_browse: Optional[str] = Field(..., alias='lastBrowse')
    last_tracker: Any = Field(..., alias='lastTracker')
    last_change_pwd: Any = Field(..., alias='lastChangePwd')


class MemberCount(BaseModel):
    created_date: Optional[str] = Field(..., alias='createdDate')
    last_modified_date: Optional[str] = Field(..., alias='lastModifiedDate')
    id: Optional[str]
    bonus: Optional[str]
    uploaded: Optional[str]
    downloaded: Optional[str]
    share_rate: Optional[str] = Field(..., alias='shareRate')
    charity: Optional[str]
    upload_reset: Optional[str] = Field(..., alias='uploadReset')


class Config(BaseModel):
    tracker_domain: Any = Field(..., alias='trackerDomain')
    download_domain: Any = Field(..., alias='downloadDomain')
    rss_domain: Any = Field(..., alias='rssDomain')
    block_categories: List = Field(..., alias='blockCategories')
    hide_fun: Optional[bool] = Field(..., alias='hideFun')
    show_thumbnail: Optional[bool] = Field(..., alias='showThumbnail')
    time_type: Optional[str] = Field(..., alias='timeType')
    anonymous: Optional[bool]
    tracker_disable_seedbox: Any = Field(..., alias='trackerDisableSeedbox')


class Data(BaseModel):
    id: Optional[str]
    created_date: Optional[str] = Field(..., alias='createdDate')
    last_modified_date: Optional[str] = Field(..., alias='lastModifiedDate')
    username: Optional[str]
    email: Optional[str]
    status: Optional[str]
    enabled: Optional[bool]
    ip: Optional[str]
    country: Optional[str]
    gender: Optional[str]
    privacy: Optional[str]
    language: Any
    allow_download: Optional[bool] = Field(..., alias='allowDownload')
    member_status: MemberStatus = Field(..., alias='memberStatus')
    member_count: MemberCount = Field(..., alias='memberCount')
    parked: Optional[bool]
    parent_id: Optional[str] = Field(..., alias='parentId')
    invites: Optional[str]
    role: Optional[str]
    staff_position: Any = Field(..., alias='staffPosition')
    staff_duties: Any = Field(..., alias='staffDuties')
    roles: Any
    limit_invites: Optional[str] = Field(..., alias='limitInvites')
    info: Any
    acceptpms: Optional[str]
    deletepms: Optional[bool]
    savepms: Optional[bool]
    commentpm: Optional[bool]
    magicgivingpm: Optional[bool]
    download_speed: Optional[str] = Field(..., alias='downloadSpeed')
    upload_speed: Optional[str] = Field(..., alias='uploadSpeed')
    isp: Optional[str]
    avatar_url: Optional[str] = Field(..., alias='avatarUrl')
    title: Optional[str]
    anonymous: Optional[bool]
    enabled_tfa: Optional[bool] = Field(..., alias='enabledTfa')
    seedtime: Optional[str]
    leechtime: Optional[str]
    torrent_comment_count: Optional[str] = Field(..., alias='torrentCommentCount')
    seek_comment_count: Optional[str] = Field(..., alias='seekCommentCount')
    forum_comment_count: Optional[str] = Field(..., alias='forumCommentCount')
    ip_count: Optional[str] = Field(..., alias='ipCount')
    friend: Optional[bool]
    block: Optional[bool]
    config: Config
    authorities: List[str]
    release_code: Optional[str] = Field(..., alias='releaseCode')
    telegram_user_name: Any = Field(..., alias='telegramUserName')
    telegram_chat_id: Any = Field(..., alias='telegramChatId')


class ResponseModel(BaseModel):
    message: Optional[str] = None
    data: Optional[Data] = None
    code: Optional[str] = None

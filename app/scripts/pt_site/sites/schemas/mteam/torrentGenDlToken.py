from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

class TorrentGenDlTokenResponse(BaseModel):
    """种子生成下载令牌响应"""
    message: Optional[str] = None
    data: Optional[str] = None
    code: Optional[str | int] = None

class TorrentGenDlTokenRequest(BaseModel):
    """种子生成下载令牌请求"""
    id: int = Field(..., alias='id')



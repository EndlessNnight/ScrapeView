from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

# 通知类型
NotificationType = Literal["user", "all"]

# 创建通知请求
class NotificationCreate(BaseModel):
    title: str = Field(..., description="通知标题", max_length=100)
    content: str = Field(..., description="通知内容")
    notification_type: NotificationType = Field(..., description="通知类型: user(指定用户), all(所有用户)")
    user_id: Optional[int] = Field(None, description="指定用户ID，为空表示发送给所有用户")

# 更新通知请求
class NotificationUpdate(BaseModel):
    is_read: bool = Field(..., description="是否已读")

# 通知响应
class NotificationResponse(BaseModel):
    id: int
    title: str
    content: str
    notification_type: str
    user_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 通知列表响应
class NotificationListResponse(BaseModel):
    total: int = Field(..., description="总数")
    items: List[NotificationResponse] = Field(..., description="通知列表")

# 通知统计响应
class NotificationStats(BaseModel):
    total: int = Field(..., description="总通知数")
    unread: int = Field(..., description="未读通知数") 
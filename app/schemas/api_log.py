from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ApiLogBase(BaseModel):
    method: str
    path: str
    query_params: Optional[str] = None
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    status_code: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    duration_ms: Optional[int] = None
    has_binary_data: bool = False


class ApiLogCreate(ApiLogBase):
    pass


class ApiLog(ApiLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ApiLogFilter(BaseModel):
    path: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
    sort_by: str = "created_at"
    sort_order: str = "desc"


class ApiLogListResponse(BaseModel):
    total: int
    items: List[ApiLog] 
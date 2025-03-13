from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TaskType(str, Enum):
    """任务类型枚举"""
    SCHEDULED = "scheduled"  # 定时任务
    ONCE = "once"  # 一次性任务

class TaskFunctionInfo(BaseModel):
    """任务函数信息"""
    name: str
    description: str
    is_async: bool

class TaskFunctionListResponse(BaseModel):
    """任务函数列表响应模型"""
    total: int
    items: List[TaskFunctionInfo]

class TaskBase(BaseModel):
    name: str
    function_name: str
    task_type: TaskType = TaskType.SCHEDULED
    cron_expression: Optional[str] = None
    description: Optional[str] = None
    is_enabled: bool = True

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    function_name: Optional[str] = None
    task_type: Optional[TaskType] = None
    cron_expression: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None

class TaskResponse(TaskBase):
    id: int
    status: str
    error_message: Optional[str] = None
    last_run_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }

class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    total: int
    items: List[TaskResponse]

    class Config:
        from_attributes = True 
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.db.base_class import Base

class BackgroundTask(Base):
    __tablename__ = "background_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, comment="任务名称")
    function_name = Column(String(100), nullable=False, comment="函数名称")
    task_type = Column(String(20), default="scheduled", comment="任务类型: scheduled(定时任务) / once(一次性任务)")
    cron_expression = Column(String(100), nullable=True, comment="Cron表达式，一次性任务可为空")
    description = Column(Text, nullable=True, comment="任务描述")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    last_run_time = Column(DateTime(timezone=True), nullable=True, comment="上次运行时间")
    next_run_time = Column(DateTime(timezone=True), nullable=True, comment="下次运行时间")
    status = Column(String(20), default="idle", comment="运行状态: idle/running/error")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间") 
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.db.base import Base


class ApiLog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    method = Column(String(10), nullable=False, comment="HTTP方法")
    path = Column(String(255), nullable=False, comment="请求路径")
    query_params = Column(Text, nullable=True, comment="查询参数")
    request_body = Column(Text, nullable=True, comment="请求体")
    response_body = Column(Text, nullable=True, comment="响应体")
    status_code = Column(Integer, nullable=True, comment="状态码")
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(255), nullable=True, comment="用户代理")
    duration_ms = Column(Integer, nullable=True, comment="请求处理时间(毫秒)")
    has_binary_data = Column(Boolean, default=False, comment="是否包含二进制数据")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="创建时间") 
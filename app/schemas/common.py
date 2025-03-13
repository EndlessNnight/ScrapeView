from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "操作成功"
    data: Optional[T] = None

# 系统级错误码 (1000-1999)
class ErrorCode:
    SUCCESS = 200  # 成功
    SYSTEM_ERROR = 1000  # 系统错误
    PARAM_ERROR = 1001  # 参数错误
    NOT_FOUND = 1002  # 资源不存在
    UNAUTHORIZED = 1003  # 未授权
    FORBIDDEN = 1004  # 禁止访问
    
    # 业务错误码 (2000-2999)
    NOT_INSTALLED = 2000  # 系统未安装
    ALREADY_INSTALLED = 2001  # 系统已安装
    
    # 用户相关错误码 (3000-3999)
    USER_NOT_FOUND = 3000  # 用户不存在
    PASSWORD_ERROR = 3001  # 密码错误
    TOKEN_EXPIRED = 3002  # Token过期
    TOKEN_INVALID = 3003  # Token无效

    @staticmethod
    def get_message(code: int) -> str:
        """获取错误码对应的默认消息"""
        message_map = {
            200: "操作成功",
            1000: "系统错误",
            1001: "参数错误",
            1002: "资源不存在",
            1003: "未授权",
            1004: "禁止访问",
            2000: "系统未安装",
            2001: "系统已安装",
            3000: "用户不存在",
            3001: "密码错误",
            3002: "Token已过期",
            3003: "Token无效"
        }
        return message_map.get(code, "未知错误") 
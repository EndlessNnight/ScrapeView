from enum import IntEnum

class ErrorCode(IntEnum):
    """错误码枚举"""
    SUCCESS = 200  # 成功
    PARAM_ERROR = 400  # 参数错误
    UNAUTHORIZED = 401  # 未授权
    FORBIDDEN = 403  # 禁止访问
    NOT_FOUND = 404  # 资源不存在
    SYSTEM_ERROR = 500  # 系统错误
    INTERNAL_ERROR = 50000  # 内部错误

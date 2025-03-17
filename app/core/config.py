from pydantic import BaseModel
import os
from pathlib import Path
import logging

class Settings(BaseModel):
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3*60*60*24
    ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # 图片存储路径，默认为项目根目录下的 uploads/images 文件夹
    IMAGES_STORAGE_PATH: str = os.getenv("IMAGES_STORAGE_PATH", str(Path.cwd() / "uploads" / "images"))
    
    # 图片访问URL前缀
    IMAGES_URL_PREFIX: str = os.getenv("IMAGES_URL_PREFIX", "/api/v1/images")
    
    # HTTP代理设置
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "http://127.0.0.1:7890")
    HTTPS_PROXY: str = os.getenv("HTTPS_PROXY", "http://127.0.0.1:7890")
    # 不使用代理的域名列表
    NO_PROXY: str = os.getenv("NO_PROXY", "")
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", str(Path.cwd() / "logs"))
    
    @property
    def log_level(self) -> int:
        """获取日志级别"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(self.LOG_LEVEL.upper(), logging.INFO)
    
settings = Settings() 
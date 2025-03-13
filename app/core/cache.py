from typing import Any, Dict, Optional, Callable, Tuple
import time
import hashlib
import json
import threading
from functools import wraps


class LocalCache:
    """本地缓存实现
    
    使用内存字典存储缓存数据，支持过期时间设置
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LocalCache, cls).__new__(cls)
                cls._instance._cache = {}  # 缓存数据
                cls._instance._expiry = {}  # 过期时间
            return cls._instance
    
    def set(self, key: str, value: Any, expire_seconds: int = 300) -> None:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire_seconds: 过期时间（秒），默认5分钟
        """
        self._cache[key] = value
        if expire_seconds > 0:
            self._expiry[key] = time.time() + expire_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        # 检查是否存在
        if key not in self._cache:
            return None
            
        # 检查是否过期
        if key in self._expiry and time.time() > self._expiry[key]:
            # 已过期，删除缓存
            del self._cache[key]
            del self._expiry[key]
            return None
            
        return self._cache[key]
    
    def delete(self, key: str) -> None:
        """删除缓存
        
        Args:
            key: 缓存键
        """
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._expiry.clear()
        
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键
        
        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            生成的缓存键
        """
        # 将参数转换为字符串
        key_parts = [prefix]
        
        # 添加位置参数
        if args:
            key_parts.append(str(args))
            
        # 添加关键字参数（按键排序）
        if kwargs:
            sorted_items = sorted(kwargs.items())
            key_parts.append(str(sorted_items))
            
        # 连接并哈希
        key_str = "_".join(key_parts)
        return f"{prefix}_{hashlib.md5(key_str.encode()).hexdigest()}"


def cached(expire_seconds: int = 300, prefix: str = None):
    """缓存装饰器
    
    Args:
        expire_seconds: 过期时间（秒），默认5分钟
        prefix: 缓存键前缀，默认为函数名
        
    Returns:
        装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取缓存实例
            cache = LocalCache()
            
            # 生成缓存键
            cache_prefix = prefix or func.__name__
            cache_key = cache.generate_key(cache_prefix, *args, **kwargs)
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # 缓存未命中，执行原函数
            result = await func(*args, **kwargs)
            # 存入缓存
            cache.set(cache_key, result, expire_seconds)
            
            return result
        return wrapper
    return decorator 
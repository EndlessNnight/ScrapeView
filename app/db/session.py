from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.database_config import get_db_url as get_env_db_url
from fastapi import HTTPException
from contextlib import contextmanager
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)

# 环境变量名称常量
ENV_USE_ENV_CONFIG = "SCRAPEVIEW_USE_ENV_CONFIG"

class DatabaseSession:
    _instance = None
    _engine = None
    _session_local = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseSession, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 由于是单例，只在第一次初始化时执行
        if self._engine is None:
            self._initialize()

    def _initialize(self):
        """初始化数据库连接"""
        pass  # 初始化时不做任何事，等待显式调用set_engine

    def init_db(self):
        """主动初始化数据库"""
        try:
            db_url = get_env_db_url()
            engine = self.create_engine(db_url)
            self.set_engine(engine)
            logger.info("使用环境变量配置初始化数据库成功")
            return True
        except Exception as e:
            logger.error(f"初始化数据库失败: {str(e)}", exc_info=True)
            return False

    def get_db_url(self) -> str:
        """获取数据库连接URL"""
        return get_env_db_url()

    def create_engine(self, db_url: Optional[str] = None) -> Optional[object]:
        """创建数据库引擎"""
        try:
            url = db_url if db_url else self.get_db_url()
            
            # SQLite特殊配置
            if url.startswith("sqlite"):
                return create_engine(
                    url,
                    connect_args={"check_same_thread": False},  # 允许多线程访问
                    pool_pre_ping=True,
                    echo=False
                )
            
            # MySQL配置
            return create_engine(
                url,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=20,
                max_overflow=10,
                echo=False
            )
        except Exception as e:
            logger.error(f"创建数据库引擎失败: {str(e)}", exc_info=True)
            return None

    def set_engine(self, new_engine) -> bool:
        """设置数据库引擎"""
        try:
            # 测试数据库连接
            with new_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            
            self._engine = new_engine
            self._session_local = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine
            )
            logger.info("数据库引擎初始化成功")
            return True
        except Exception as e:
            logger.error(f"设置数据库引擎失败: {str(e)}", exc_info=True)
            return False

    @property
    def engine(self):
        """获取当前数据库引擎"""
        return self._engine

    @property
    def session_local(self):
        """获取当前会话工厂"""
        return self._session_local

    @contextmanager
    def get_db(self):
        """获取数据库会话的上下文管理器"""
        if not self._session_local:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available. Please initialize database first."
            )
        
        db = self._session_local()
        try:
            yield db
        finally:
            db.close()

# 创建全局单例实例
base_db = DatabaseSession()

# 为了保持与现有代码的兼容性，提供以下函数
def get_db_url() -> str:
    return base_db.get_db_url()

def create_db_engine(db_url: Optional[str] = None) -> Optional[object]:
    return base_db.create_engine(db_url)

def set_db_engine(new_engine) -> bool:
    return base_db.set_engine(new_engine)

@contextmanager
def get_db_context():
    """保持向后兼容的上下文管理器"""
    with base_db.get_db() as session:
        yield session

def get_db():
    """FastAPI依赖注入使用的数据库会话获取器"""
    with get_db_context() as session:
        yield session 

if __name__ == "__main__":
    from app.crud.douyin import get_pending_video_files
    base_db.init_db()
    with base_db.get_db() as session:
        print(get_pending_video_files(session))

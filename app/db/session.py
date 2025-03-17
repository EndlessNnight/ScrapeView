from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from app.core.database_config import get_db_url as get_env_db_url
from fastapi import HTTPException
from contextlib import contextmanager
import logging
from typing import Optional
import os
import time
import threading

logger = logging.getLogger(__name__)

# 环境变量名称常量
ENV_USE_ENV_CONFIG = "SCRAPEVIEW_USE_ENV_CONFIG"

# 存储定时器对象的全局变量
pool_monitor_timer = None

# 添加连接池监控
def add_engine_monitoring(engine):
    """添加数据库引擎监控"""
    global pool_monitor_timer
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        connection_record.info.setdefault('checkout_time', time.time())
        
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        checkout_time = connection_record.info.get('checkout_time')
        if checkout_time is not None:
            connection_record.info.pop('checkout_time')
            total_time = time.time() - checkout_time
            if total_time > 5:  # 记录持有时间超过5秒的连接
                logger.warning(f"数据库连接持有时间过长: {total_time:.2f}秒")
    
    # 每10分钟记录一次连接池状态
    def log_pool_status():
        try:
            # 使用更安全的方式获取连接池状态
            status = {
                "pool_size": engine.pool.size()
            }
            
            # 尝试获取超时设置
            try:
                status["pool_timeout"] = engine.pool._timeout
            except:
                pass
            
            # 尝试获取回收时间
            try:
                status["pool_recycle"] = engine.pool._recycle
            except:
                pass
            
            # 尝试获取其他可能的属性
            try:
                status["checkedin"] = engine.pool._pool.qsize()
            except:
                pass
            
            try:
                status["overflow"] = engine.pool._overflow
            except:
                pass
            
            try:
                status["max_overflow"] = engine.pool._max_overflow
            except:
                pass
            
            logger.info(f"数据库连接池状态: {status}")
        except Exception as e:
            logger.error(f"记录连接池状态失败: {str(e)}", exc_info=True)
    
    # 设置定时器
    from threading import Timer
    def schedule_log():
        global pool_monitor_timer
        log_pool_status()
        # 创建新的定时器
        pool_monitor_timer = Timer(600, schedule_log)  # 每10分钟执行一次
        pool_monitor_timer.daemon = True  # 设置为守护线程，这样主线程退出时它会自动退出
        pool_monitor_timer.start()
    
    # 如果已有定时器，先取消
    if pool_monitor_timer is not None:
        try:
            pool_monitor_timer.cancel()
            logger.info("已取消旧的数据库连接池监控定时器")
        except:
            pass
    
    # 启动定时器
    pool_monitor_timer = Timer(10, schedule_log)  # 10秒后开始第一次执行
    pool_monitor_timer.daemon = True  # 设置为守护线程
    pool_monitor_timer.start()
    logger.info("数据库连接池监控定时器已启动")

# 关闭连接池监控定时器
def stop_pool_monitoring():
    """停止数据库连接池监控定时器"""
    global pool_monitor_timer
    if pool_monitor_timer is not None:
        try:
            pool_monitor_timer.cancel()
            logger.info("数据库连接池监控定时器已停止")
        except Exception as e:
            logger.error(f"停止数据库连接池监控定时器时出错: {str(e)}")
        pool_monitor_timer = None

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
                engine = create_engine(
                    url,
                    connect_args={"check_same_thread": False},  # 允许多线程访问
                    pool_pre_ping=True,
                    echo=False
                )
            else:
                # MySQL配置
                pool_size = 50       # 增加连接池大小
                max_overflow = 30    # 增加最大溢出连接数
                pool_recycle = 1800  # 减少连接回收时间为30分钟
                pool_timeout = 20    # 减少连接超时时间
                
                logger.info(f"创建MySQL连接池，配置: pool_size={pool_size}, max_overflow={max_overflow}, pool_recycle={pool_recycle}, pool_timeout={pool_timeout}")
                
                engine = create_engine(
                    url,
                    pool_pre_ping=True,
                    pool_recycle=pool_recycle,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_timeout=pool_timeout,
                    echo=False
                )
            
            # 添加连接池监控
            add_engine_monitoring(engine)
            
            return engine
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
        start_time = time.time()
        try:
            yield db
        finally:
            # 检查会话持有时间
            elapsed = time.time() - start_time
            if elapsed > 5:  # 如果会话持有时间超过5秒，记录警告
                logger.warning(f"数据库会话持有时间过长: {elapsed:.2f}秒")
            
            # 确保会话被关闭
            try:
                db.close()
            except Exception as e:
                logger.error(f"关闭数据库会话时出错: {str(e)}")

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
    db = None
    start_time = time.time()
    try:
        db = base_db.session_local()
        yield db
    finally:
        # 检查会话持有时间
        elapsed = time.time() - start_time
        if elapsed > 5:  # 如果会话持有时间超过5秒，记录警告
            logger.warning(f"FastAPI依赖注入数据库会话持有时间过长: {elapsed:.2f}秒")
        
        # 确保会话被关闭
        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"关闭FastAPI依赖注入数据库会话时出错: {str(e)}")

if __name__ == "__main__":
    from app.crud.douyin import get_pending_video_files
    base_db.init_db()
    with base_db.get_db() as session:
        print(get_pending_video_files(session))

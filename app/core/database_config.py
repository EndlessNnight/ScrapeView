import os
import pathlib
from typing import Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import logging

# 加载.env文件中的环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# 环境变量名称常量
ENV_PREFIX = "SCRAPEVIEW_"
ENV_DB_HOST = f"{ENV_PREFIX}DB_HOST"
ENV_DB_PORT = f"{ENV_PREFIX}DB_PORT"
ENV_DB_USER = f"{ENV_PREFIX}DB_USER"
ENV_DB_PASSWORD = f"{ENV_PREFIX}DB_PASSWORD"
ENV_DB_NAME = f"{ENV_PREFIX}DB_NAME"
ENV_ENVIRONMENT = f"{ENV_PREFIX}ENVIRONMENT"
ENV_DB_TYPE = f"{ENV_PREFIX}DB_TYPE"
ENV_SQLITE_PATH = f"{ENV_PREFIX}SQLITE_PATH"

# 数据库类型
DB_TYPE_MYSQL = "mysql"
DB_TYPE_SQLITE = "sqlite"

# 默认开发环境配置
DEFAULT_DEV_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "username": "root",
    "password": "root",
    "database": "scrape_view_dev"
}

# 默认生产环境配置
DEFAULT_PROD_CONFIG = {
    "host": "r.luckynex.cn",
    "port": 4313,
    "username": "tiktok",
    "password": "qweqwe123",
    "database": "scrape_view"
}

# SQLite默认配置
DEFAULT_SQLITE_PATH = "sqlite.db"

class DatabaseConfig(BaseModel):
    """数据库配置模型"""
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    db_type: str = DB_TYPE_MYSQL
    sqlite_path: Optional[str] = None

def get_environment() -> str:
    """获取当前环境"""
    return os.getenv(ENV_ENVIRONMENT, "development").lower()

def is_production() -> bool:
    """检查是否是生产环境"""
    return get_environment() in ["production", "prod"]

def get_sqlite_path() -> str:
    """获取SQLite数据库路径"""
    # 从环境变量获取SQLite路径
    sqlite_path = os.getenv(ENV_SQLITE_PATH)
    if not sqlite_path:
        # 如果未设置，使用默认路径
        base_dir = pathlib.Path(__file__).parent.parent.parent
        sqlite_path = str(base_dir / DEFAULT_SQLITE_PATH)
    
    # 将路径转换为绝对路径
    abs_sqlite_path = os.path.abspath(sqlite_path)
    
    # 获取数据库文件所在的目录路径
    db_dir = os.path.dirname(abs_sqlite_path)
    
    try:
        # 如果目录不存在，创建目录（包括所有必要的父目录）
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"创建SQLite数据库目录: {db_dir}")
    except Exception as e:
        logger.error(f"创建SQLite数据库目录失败: {str(e)}")
        raise Exception(f"无法创建SQLite数据库目录 {db_dir}: {str(e)}")
    
    return abs_sqlite_path

def get_db_config() -> DatabaseConfig:
    """
    获取数据库配置，优先级：
    1. 环境变量中的数据库类型
    2. 如果是MySQL，使用环境变量或默认配置
    3. 如果是SQLite，使用环境变量中的路径或默认路径
    """
    # 获取数据库类型
    db_type = os.getenv(ENV_DB_TYPE, DB_TYPE_MYSQL).lower()
    
    # 如果是SQLite
    if db_type == DB_TYPE_SQLITE:
        sqlite_path = get_sqlite_path()
        logger.info(f"使用SQLite数据库: {sqlite_path}")
        return DatabaseConfig(
            db_type=DB_TYPE_SQLITE,
            sqlite_path=sqlite_path
        )
    
    # 如果是MySQL
    # 确定基础配置
    base_config = DEFAULT_PROD_CONFIG if is_production() else DEFAULT_DEV_CONFIG
    
    # 从环境变量覆盖配置
    config = {
        "host": os.getenv(ENV_DB_HOST, base_config["host"]),
        "port": int(os.getenv(ENV_DB_PORT, str(base_config["port"]))),
        "username": os.getenv(ENV_DB_USER, base_config["username"]),
        "password": os.getenv(ENV_DB_PASSWORD, base_config["password"]),
        "database": os.getenv(ENV_DB_NAME, base_config["database"]),
        "db_type": DB_TYPE_MYSQL
    }
    
    logger.info(f"当前环境: {get_environment()}, MySQL数据库: {config['host']}:{config['port']}/{config['database']}")
    
    return DatabaseConfig(**config)

def get_db_url() -> str:
    """获取数据库连接URL"""
    config = get_db_config()
    
    # 根据数据库类型返回不同的连接URL
    if config.db_type == DB_TYPE_SQLITE:
        return f"sqlite:///{config.sqlite_path}"
    else:
        return f"mysql+pymysql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"

def is_mysql_configured() -> bool:
    """检查是否配置了MySQL数据库"""
    # 如果明确指定了使用SQLite，返回False
    if os.getenv(ENV_DB_TYPE, "").lower() == DB_TYPE_SQLITE:
        return False
    
    # 检查MySQL配置是否完整
    host = os.getenv(ENV_DB_HOST)
    port = os.getenv(ENV_DB_PORT)
    user = os.getenv(ENV_DB_USER)
    password = os.getenv(ENV_DB_PASSWORD)
    database = os.getenv(ENV_DB_NAME)
    
    # 如果所有MySQL配置都存在，返回True
    if host and port and user and password and database:
        return True
    
    return False 
import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_dir="logs"):
    """
    设置日志配置，将日志输出到控制台和文件
    
    Args:
        log_level: 日志级别，默认为INFO
        log_dir: 日志文件目录，默认为logs
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 创建文件处理器 - 常规日志
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_path / f"app_{today}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # 创建文件处理器 - 错误日志
    error_log_file = log_path / f"error_{today}.log"
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)
    
    # 添加处理器到根日志记录器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_file_handler)
    
    # 设置特定模块的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # 记录初始日志消息
    logging.info(f"日志系统初始化完成，日志文件保存在: {log_path.absolute()}")
    logging.info(f"日志级别: {logging.getLevelName(log_level)}")
    
    return root_logger

def get_logger(name):
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name) 
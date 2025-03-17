from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db, base_db
from app.schemas.common import ApiResponse
from app.core.config import settings
from typing import Dict, Any
import logging
import time
import psutil
import os
import sys
import importlib
from pathlib import Path
import subprocess

router = APIRouter()

@router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查接口，返回系统状态信息
    
    包括：
    - 数据库连接池状态
    - 系统资源使用情况
    - 应用运行时间
    - 图片缓存统计
    """
    start_time = time.time()
    
    # 检查数据库连接
    try:
        # 执行简单查询测试数据库连接
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # 获取数据库连接池状态
    pool_status = {}
    if base_db.engine and hasattr(base_db.engine, "pool"):
        pool = base_db.engine.pool
        pool_status["size"] = pool.size()
        
        # 尝试获取其他可能的属性
        try:
            pool_status["timeout"] = pool._timeout
        except:
            pass
            
        try:
            pool_status["recycle"] = pool._recycle
        except:
            pass
            
        try:
            pool_status["checkedin"] = pool._pool.qsize()
        except:
            pass
            
        try:
            pool_status["overflow"] = pool._overflow
        except:
            pass
            
        try:
            pool_status["max_overflow"] = pool._max_overflow
        except:
            pass
    
    # 获取系统资源使用情况
    system_info = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }
    
    # 获取进程信息
    process = psutil.Process(os.getpid())
    process_info = {
        "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(),
        "threads": process.num_threads(),
        "open_files": len(process.open_files()),
        "connections": len(process.connections()),
    }
    
    # 获取图片缓存统计信息
    cache_stats = {}
    try:
        # 动态导入图片缓存模块
        pt_site_module = importlib.import_module("app.api.v1.endpoints.pt_site")
        if hasattr(pt_site_module, "image_cache"):
            cache_stats = pt_site_module.image_cache.get_stats()
        
        # 获取限流器统计信息
        if hasattr(pt_site_module, "image_rate_limiter"):
            cache_stats["rate_limiter"] = pt_site_module.image_rate_limiter.get_stats()
    except Exception as e:
        logging.error(f"获取图片缓存统计信息失败: {str(e)}")
    
    # 计算响应时间
    response_time = time.time() - start_time
    
    return ApiResponse(
        code=200,
        message="Health check completed",
        data={
            "status": "ok" if db_status == "healthy" else "error",
            "database": {
                "status": db_status,
                "pool": pool_status
            },
            "system": system_info,
            "process": process_info,
            "cache": cache_stats,
            "response_time_ms": round(response_time * 1000, 2)
        }
    )

@router.get("/db-pool", response_model=ApiResponse[Dict[str, Any]])
async def db_pool_status():
    """
    获取数据库连接池状态
    
    返回详细的连接池信息，包括连接数、使用情况等
    """
    pool_status = {}
    if base_db.engine and hasattr(base_db.engine, "pool"):
        pool = base_db.engine.pool
        
        # 基本信息
        pool_status["size"] = pool.size()
        pool_status["overflow"] = getattr(pool, "_overflow", "unknown")
        pool_status["max_overflow"] = getattr(pool, "_max_overflow", "unknown")
        pool_status["timeout"] = getattr(pool, "_timeout", "unknown")
        pool_status["recycle"] = getattr(pool, "_recycle", "unknown")
        
        # 连接使用情况
        try:
            pool_status["checkedin"] = pool._pool.qsize() if hasattr(pool, "_pool") else "unknown"
        except:
            pool_status["checkedin"] = "error"
            
        # 其他可能的属性
        for attr_name in dir(pool):
            if not attr_name.startswith("_") and attr_name not in pool_status:
                attr = getattr(pool, attr_name)
                if isinstance(attr, (int, float, str, bool)) or attr is None:
                    pool_status[attr_name] = attr
    
    return ApiResponse(
        code=200,
        message="Database pool status",
        data=pool_status
    )

@router.post("/db-pool/dispose", response_model=ApiResponse[Dict[str, Any]])
async def dispose_db_pool():
    """
    释放并重新创建数据库连接池
    
    警告：这将关闭所有现有连接，可能导致正在进行的操作失败
    仅在连接池出现问题时使用
    """
    result = {
        "old_pool": {},
        "new_pool": {},
        "success": False
    }
    
    # 获取旧连接池状态
    if base_db.engine and hasattr(base_db.engine, "pool"):
        pool = base_db.engine.pool
        result["old_pool"]["size"] = pool.size()
        result["old_pool"]["overflow"] = getattr(pool, "_overflow", "unknown")
    
    try:
        # 释放旧连接池
        if base_db.engine:
            base_db.engine.dispose()
            logging.warning("数据库连接池已释放")
        
        # 重新初始化数据库
        if base_db.init_db():
            logging.info("数据库连接池已重新创建")
            result["success"] = True
            
            # 获取新连接池状态
            if base_db.engine and hasattr(base_db.engine, "pool"):
                pool = base_db.engine.pool
                result["new_pool"]["size"] = pool.size()
                result["new_pool"]["overflow"] = getattr(pool, "_overflow", "unknown")
        else:
            logging.error("重新创建数据库连接池失败")
    except Exception as e:
        logging.error(f"释放并重新创建数据库连接池时出错: {str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message=f"释放并重新创建数据库连接池失败: {str(e)}",
            data=result
        )
    
    return ApiResponse(
        code=200,
        message="数据库连接池已释放并重新创建" if result["success"] else "操作失败",
        data=result
    )

@router.get("/logs", response_model=ApiResponse[Dict[str, Any]])
async def get_logs(
    log_type: str = Query("app", description="日志类型，app或error"),
    lines: int = Query(100, ge=1, le=1000, description="返回的日志行数"),
    date: str = Query(None, description="日志日期，格式为YYYY-MM-DD，默认为今天")
):
    """
    获取应用日志
    
    返回指定类型和日期的日志内容
    """
    from datetime import datetime
    import os
    from pathlib import Path
    
    # 获取日志目录
    log_dir = Path(settings.LOG_DIR)
    
    # 确定日期
    if date:
        try:
            log_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return ApiResponse(
                code=400,
                message=f"无效的日期格式: {date}，正确格式为YYYY-MM-DD",
                data=None
            )
    else:
        log_date = datetime.now().strftime("%Y-%m-%d")
    
    # 确定日志文件
    if log_type.lower() == "error":
        log_file = log_dir / f"error_{log_date}.log"
    else:
        log_file = log_dir / f"app_{log_date}.log"
    
    # 检查日志文件是否存在
    if not log_file.exists():
        return ApiResponse(
            code=404,
            message=f"日志文件不存在: {log_file.name}",
            data={
                "available_logs": [f.name for f in log_dir.glob("*.log")]
            }
        )
    
    # 读取日志内容
    try:
        # 使用tail命令获取最后N行
        result = subprocess.run(
            ["tail", "-n", str(lines), str(log_file)],
            capture_output=True,
            text=True,
            check=True
        )
        log_content = result.stdout.splitlines()
        
        return ApiResponse(
            code=200,
            message=f"获取日志成功: {log_file.name}",
            data={
                "log_file": log_file.name,
                "lines": len(log_content),
                "content": log_content
            }
        )
    except subprocess.CalledProcessError as e:
        return ApiResponse(
            code=500,
            message=f"读取日志文件失败: {str(e)}",
            data={
                "error": str(e),
                "stderr": e.stderr
            }
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"读取日志文件失败: {str(e)}",
            data=None
        )

@router.get("/logs/files", response_model=ApiResponse[Dict[str, Any]])
async def get_log_files():
    """
    获取所有日志文件列表
    
    返回日志目录中的所有日志文件
    """
    from pathlib import Path
    import os
    
    # 获取日志目录
    log_dir = Path(settings.LOG_DIR)
    
    # 检查日志目录是否存在
    if not log_dir.exists():
        return ApiResponse(
            code=404,
            message=f"日志目录不存在: {log_dir}",
            data=None
        )
    
    # 获取所有日志文件
    log_files = []
    for file in log_dir.glob("*.log"):
        log_files.append({
            "name": file.name,
            "size": file.stat().st_size,
            "modified": file.stat().st_mtime,
            "created": file.stat().st_ctime
        })
    
    # 按修改时间排序
    log_files.sort(key=lambda x: x["modified"], reverse=True)
    
    return ApiResponse(
        code=200,
        message="获取日志文件列表成功",
        data={
            "log_dir": str(log_dir),
            "files": log_files
        }
    ) 
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.endpoints import auth, douyin, task, api_log, notification, user, pt_site, health, cookiecloud
from app.core.config import settings
from app.schemas.common import ApiResponse, ErrorCode
from app.db.session import base_db, stop_pool_monitoring
from app.db.base import Base
from app.core.scheduler import init_scheduler, shutdown_scheduler
from app.core.middleware import APILoggingMiddleware
from app.core.logging_config import setup_logging
from contextlib import asynccontextmanager
import logging
import os
import sys

# 初始化日志配置
setup_logging(log_level=settings.log_level, log_dir=settings.LOG_DIR)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # 初始化数据库引擎
        if base_db.init_db():
            # 确保所有表已创建
            Base.metadata.create_all(base_db.engine)
            # 初始化任务调度器
            init_scheduler()
            logger.info("应用启动成功：数据库和调度器已初始化")
        else:
            logger.error("应用启动失败：数据库初始化失败")
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}", exc_info=True)
        raise
    yield
    # 关闭资源
    try:
        # 关闭调度器
        await shutdown_scheduler()
        
        # 停止数据库连接池监控定时器
        stop_pool_monitoring()
        
        # 关闭数据库连接
        if base_db.session_local:
            base_db.session_local().close()
            
        logger.info("应用关闭：资源已释放")
    except Exception as e:
        logger.error(f"关闭资源时出错: {str(e)}", exc_info=True)


app = FastAPI(title="Data Collection API", lifespan=lifespan)

# 添加API日志中间件
app.add_middleware(
    APILoggingMiddleware,
    exclude_paths=["/docs", "/redoc", "/openapi.json", "/v1/logs"]  # 排除不需要记录的路径
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # 检查是否是自定义的Token失效响应
    if isinstance(exc.detail, dict) and "code" in exc.detail and exc.detail["code"] == 9999:
        # 直接返回自定义的响应格式
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # 处理其他HTTP异常
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            code=exc.status_code,
            message=str(exc.detail),
            data=None
        ).model_dump()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=str(exc),
            data=None
        ).model_dump()
    )

# 注册认证路由
app.include_router(auth.router, prefix="/v1", tags=["认证"])

# 注册用户路由
app.include_router(user.router, prefix="/v1/user", tags=["用户"])

# 注册抖音相关路由
app.include_router(douyin.router, prefix="/v1/douyin", tags=["抖音"])

# 注册任务路由
app.include_router(task.router, prefix="/v1", tags=["任务"])

# 注册API日志路由
app.include_router(api_log.router, prefix="/v1", tags=["日志"])

# 注册通知路由
app.include_router(notification.router, prefix="/v1/notifications", tags=["通知"])

# 注册PT站点路由
app.include_router(pt_site.router, prefix="/v1/pt_site", tags=["PT站点"])

# 注册CookieCloud路由
app.include_router(cookiecloud.router, prefix="/v1/cookiecloud", tags=["CookieCloud"])

# 添加健康检查路由
app.include_router(health.router, prefix="/v1", tags=["系统"])

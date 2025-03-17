import time
import json
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.db.session import base_db
from app.models.api_log import ApiLog
from typing import Callable, Dict, Any, Optional
import traceback

logger = logging.getLogger(__name__)


class APILoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要排除此路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # 记录请求开始时间
        start_time = time.time()
        
        # 收集请求信息
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # 记录请求信息到控制台
        logger.info(f"请求: {method} {path} - IP: {ip_address}")
        if query_params:
            logger.debug(f"查询参数: {query_params}")
        
        # 尝试读取请求体
        request_body = None
        has_binary_data = False
        
        if method in ["POST", "PUT", "PATCH"]:
            try:
                # 克隆请求体以便后续处理
                body_bytes = await request.body()
                # 重置请求体以便后续中间件和路由处理
                request._body = body_bytes
                
                # 尝试解析为JSON
                try:
                    body_str = body_bytes.decode("utf-8")
                    request_body = body_str
                    # 检查是否为JSON
                    json.loads(body_str)
                    logger.debug(f"请求体: {body_str[:200]}{'...' if len(body_str) > 200 else ''}")
                except UnicodeDecodeError:
                    # 二进制数据
                    has_binary_data = True
                    request_body = "二进制数据，未记录"
                    logger.debug("请求体: 二进制数据")
                except json.JSONDecodeError:
                    # 非JSON数据，但仍是文本
                    logger.debug(f"请求体(非JSON): {body_str[:200]}{'...' if len(body_str) > 200 else ''}")
            except Exception as e:
                logger.error(f"读取请求体时出错: {str(e)}")
                request_body = "读取请求体时出错"
        
        # 自定义响应类，用于捕获响应体
        response_body = None
        status_code = None
        
        # 处理请求并捕获响应
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # 尝试读取响应体
            response_body_bytes = b""
            async for chunk in response.body_iterator:
                response_body_bytes += chunk
            
            # 重建响应
            response = Response(
                content=response_body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            # 尝试解析响应体
            try:
                response_body = response_body_bytes.decode("utf-8")
            except UnicodeDecodeError:
                has_binary_data = True
                response_body = "二进制数据，未记录"
        except Exception as e:
            logger.error(f"处理请求时出错: {str(e)}")
            traceback.print_exc()
            # 如果出错，继续处理请求但不记录响应体
            response = await call_next(request)
            status_code = response.status_code
            response_body = f"记录响应体时出错: {str(e)}"
        
        # 计算请求处理时间
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 记录响应信息到控制台
        logger.info(f"响应: {method} {path} - 状态码: {status_code} - 耗时: {duration_ms}ms")
        
        # 异步保存日志到数据库
        try:
            self._save_log(
                method=method,
                path=path,
                query_params=json.dumps(query_params) if query_params else None,
                request_body=request_body,
                response_body=response_body,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms,
                has_binary_data=has_binary_data
            )
        except Exception as e:
            logger.error(f"保存API日志时出错: {str(e)}")
            traceback.print_exc()
        
        return response
    
    def _save_log(self, **kwargs):
        """保存日志到数据库"""
        try:
            with base_db.get_db() as db:
                log_entry = ApiLog(**kwargs)
                db.add(log_entry)
                db.commit()
        except Exception as e:
            logger.error(f"保存日志到数据库时出错: {str(e)}")
            traceback.print_exc() 
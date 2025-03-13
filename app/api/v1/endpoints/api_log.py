from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.session import get_db
from app.crud import api_log
from app.schemas.api_log import ApiLog as ApiLogSchema, ApiLogFilter, ApiLogListResponse
from app.schemas.common import ApiResponse
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/logs", response_model=ApiResponse[ApiLogListResponse])
async def get_api_logs(
    filter_params: ApiLogFilter = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取API访问日志列表，支持分页、过滤和排序
    """
    logs = api_log.get_api_logs(
        db=db,
        skip=filter_params.skip,
        limit=filter_params.limit,
        path=filter_params.path,
        method=filter_params.method,
        status_code=filter_params.status_code,
        start_time=filter_params.start_time,
        end_time=filter_params.end_time,
        sort_by=filter_params.sort_by,
        sort_order=filter_params.sort_order
    )
    
    total = api_log.count_api_logs(
        db=db,
        path=filter_params.path,
        method=filter_params.method,
        status_code=filter_params.status_code,
        start_time=filter_params.start_time,
        end_time=filter_params.end_time
    )
    
    return ApiResponse(
        code=200,
        message="获取API日志成功",
        data=ApiLogListResponse(
            total=total,
            items=logs
        )
    )


@router.get("/logs/{log_id}", response_model=ApiResponse[ApiLogSchema])
async def get_api_log_by_id(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    通过ID获取单个API日志详情
    """
    log = api_log.get_api_log_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    return ApiResponse(
        code=200,
        message="获取API日志详情成功",
        data=log
    )


@router.delete("/logs", response_model=ApiResponse)
async def delete_old_logs(
    days: int = Query(30, description="删除多少天前的日志", ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除指定天数之前的日志
    """
    before_date = datetime.now() - timedelta(days=days)
    deleted_count = api_log.delete_old_logs(db, before_date)
    
    return ApiResponse(
        code=200,
        message=f"成功删除 {deleted_count} 条日志",
        data={"deleted_count": deleted_count}
    )


@router.delete("/logs/{log_id}", response_model=ApiResponse)
async def delete_log_by_id(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    通过ID删除单个API日志
    """
    success = api_log.delete_log_by_id(db, log_id)
    if not success:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    return ApiResponse(
        code=200,
        message="删除日志成功",
        data={"log_id": log_id}
    ) 
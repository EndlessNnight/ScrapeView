from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.models.api_log import ApiLog
from typing import List, Optional, Dict, Any
from datetime import datetime


def get_api_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    path: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> List[ApiLog]:
    """
    获取API日志列表，支持分页、过滤和排序
    """
    query = db.query(ApiLog)
    
    # 应用过滤条件
    if path:
        query = query.filter(ApiLog.path.like(f"%{path}%"))
    if method:
        query = query.filter(ApiLog.method == method)
    if status_code:
        query = query.filter(ApiLog.status_code == status_code)
    if start_time:
        query = query.filter(ApiLog.created_at >= start_time)
    if end_time:
        query = query.filter(ApiLog.created_at <= end_time)
    
    # 应用排序
    if sort_order.lower() == "asc":
        query = query.order_by(asc(getattr(ApiLog, sort_by)))
    else:
        query = query.order_by(desc(getattr(ApiLog, sort_by)))
    
    # 应用分页
    return query.offset(skip).limit(limit).all()


def get_api_log_by_id(db: Session, log_id: int) -> Optional[ApiLog]:
    """
    通过ID获取单个API日志
    """
    return db.query(ApiLog).filter(ApiLog.id == log_id).first()


def count_api_logs(
    db: Session,
    path: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> int:
    """
    计算符合条件的API日志数量
    """
    query = db.query(ApiLog)
    
    # 应用过滤条件
    if path:
        query = query.filter(ApiLog.path.like(f"%{path}%"))
    if method:
        query = query.filter(ApiLog.method == method)
    if status_code:
        query = query.filter(ApiLog.status_code == status_code)
    if start_time:
        query = query.filter(ApiLog.created_at >= start_time)
    if end_time:
        query = query.filter(ApiLog.created_at <= end_time)
    
    return query.count()


def delete_old_logs(db: Session, before_date: datetime) -> int:
    """
    删除指定日期之前的日志
    """
    result = db.query(ApiLog).filter(ApiLog.created_at < before_date).delete()
    db.commit()
    return result


def delete_log_by_id(db: Session, log_id: int) -> bool:
    """
    通过ID删除单个API日志
    
    Args:
        db: 数据库会话
        log_id: 日志ID
        
    Returns:
        bool: 删除成功返回True，日志不存在返回False
    """
    log = db.query(ApiLog).filter(ApiLog.id == log_id).first()
    if not log:
        return False
    
    db.delete(log)
    db.commit()
    return True 
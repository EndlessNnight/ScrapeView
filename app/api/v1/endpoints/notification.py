from fastapi import APIRouter, Depends, HTTPException, Query, Path as PathParam
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.core.security import get_current_user
from app.schemas.notification import (
    NotificationCreate, 
    NotificationUpdate, 
    NotificationResponse, 
    NotificationListResponse,
    NotificationStats
)
from app.schemas.douyin import ApiResponse
from app.crud import notification as notification_crud
from app.models.user import User

router = APIRouter()

@router.post("", response_model=ApiResponse[NotificationResponse])
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建通知
    
    - 管理员可以创建发送给指定用户或所有用户的通知
    - 普通用户无权创建通知
    """
    # TODO: 添加管理员权限检查
    
    # 验证用户ID
    if notification.notification_type == "user" and not notification.user_id:
        raise HTTPException(status_code=400, detail="指定用户通知必须提供用户ID")
    
    db_notification = notification_crud.create_notification(db, notification)
    return ApiResponse(
        code=200,
        message="创建通知成功",
        data=db_notification
    )

@router.get("", response_model=ApiResponse[NotificationListResponse])
async def get_notifications(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回记录数"),
    only_unread: bool = Query(False, description="是否只返回未读通知"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的通知列表"""
    notifications = notification_crud.get_notifications_for_user(
        db, current_user.id, skip, limit, only_unread
    )
    total = notification_crud.count_notifications_for_user(
        db, current_user.id, only_unread
    )
    
    return ApiResponse(
        code=200,
        message="获取通知列表成功",
        data=NotificationListResponse(
            total=total,
            items=notifications
        )
    )

@router.get("/stats", response_model=ApiResponse[NotificationStats])
async def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的通知统计信息"""
    total = notification_crud.count_notifications_for_user(db, current_user.id)
    unread = notification_crud.count_notifications_for_user(db, current_user.id, only_unread=True)
    
    return ApiResponse(
        code=200,
        message="获取通知统计成功",
        data=NotificationStats(
            total=total,
            unread=unread
        )
    )

@router.get("/{notification_id}", response_model=ApiResponse[NotificationResponse])
async def get_notification(
    notification_id: int = PathParam(..., description="通知ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个通知详情"""
    db_notification = notification_crud.get_notification(db, notification_id)
    if not db_notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 检查权限：只能查看发给自己的或所有人的通知
    if (db_notification.notification_type == "user" and 
        db_notification.user_id != current_user.id and 
        db_notification.notification_type != "all"):
        raise HTTPException(status_code=403, detail="无权查看此通知")
    
    return ApiResponse(
        code=200,
        message="获取通知成功",
        data=db_notification
    )

@router.patch("/{notification_id}", response_model=ApiResponse[NotificationResponse])
async def update_notification(
    notification_update: NotificationUpdate,
    notification_id: int = PathParam(..., description="通知ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知状态（标记为已读/未读）"""
    db_notification = notification_crud.get_notification(db, notification_id)
    if not db_notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 检查权限：只能更新发给自己的或所有人的通知
    if (db_notification.notification_type == "user" and 
        db_notification.user_id != current_user.id and 
        db_notification.notification_type != "all"):
        raise HTTPException(status_code=403, detail="无权更新此通知")
    
    updated_notification = notification_crud.update_notification(
        db, notification_id, notification_update
    )
    
    return ApiResponse(
        code=200,
        message="更新通知成功",
        data=updated_notification
    )

@router.post("/mark-all-read", response_model=ApiResponse)
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将所有通知标记为已读"""
    count = notification_crud.mark_all_as_read(db, current_user.id)
    
    return ApiResponse(
        code=200,
        message=f"已将{count}条通知标记为已读",
        data=None
    )

@router.delete("/{notification_id}", response_model=ApiResponse)
async def delete_notification(
    notification_id: int = PathParam(..., description="通知ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知（管理员功能）"""
    # TODO: 添加管理员权限检查
    
    success = notification_crud.delete_notification(db, notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    return ApiResponse(
        code=200,
        message="删除通知成功",
        data=None
    ) 
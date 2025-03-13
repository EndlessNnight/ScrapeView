from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate

def create_notification(db: Session, notification: NotificationCreate) -> Notification:
    """创建通知"""
    db_notification = Notification(
        title=notification.title,
        content=notification.content,
        notification_type=notification.notification_type,
        user_id=notification.user_id if notification.notification_type == "user" else None
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notification(db: Session, notification_id: int) -> Optional[Notification]:
    """获取单个通知"""
    return db.query(Notification).filter(Notification.id == notification_id).first()

def get_notifications_for_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    only_unread: bool = False
) -> List[Notification]:
    """获取用户的通知列表"""
    query = db.query(Notification).filter(
        or_(
            Notification.notification_type == "all",
            and_(
                Notification.notification_type == "user",
                Notification.user_id == user_id
            )
        )
    )
    
    if only_unread:
        query = query.filter(Notification.is_read == False)
    
    return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

def count_notifications_for_user(
    db: Session, 
    user_id: int,
    only_unread: bool = False
) -> int:
    """统计用户的通知数量"""
    query = db.query(Notification).filter(
        or_(
            Notification.notification_type == "all",
            and_(
                Notification.notification_type == "user",
                Notification.user_id == user_id
            )
        )
    )
    
    if only_unread:
        query = query.filter(Notification.is_read == False)
    
    return query.count()

def update_notification(
    db: Session, 
    notification_id: int, 
    notification_update: NotificationUpdate
) -> Optional[Notification]:
    """更新通知状态"""
    db_notification = get_notification(db, notification_id)
    if db_notification:
        for key, value in notification_update.model_dump().items():
            setattr(db_notification, key, value)
        db.commit()
        db.refresh(db_notification)
    return db_notification

def mark_all_as_read(db: Session, user_id: int) -> int:
    """将用户的所有通知标记为已读"""
    notifications = db.query(Notification).filter(
        or_(
            Notification.notification_type == "all",
            and_(
                Notification.notification_type == "user",
                Notification.user_id == user_id
            )
        ),
        Notification.is_read == False
    ).all()
    
    count = 0
    for notification in notifications:
        notification.is_read = True
        count += 1
    
    db.commit()
    return count

def delete_notification(db: Session, notification_id: int) -> bool:
    """删除通知"""
    db_notification = get_notification(db, notification_id)
    if db_notification:
        db.delete(db_notification)
        db.commit()
        return True
    return False 
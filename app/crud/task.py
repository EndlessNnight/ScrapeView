from sqlalchemy.orm import Session
from app.models.task import BackgroundTask
from app.schemas.task import TaskCreate, TaskUpdate
from app.core.scheduler import schedule_task, get_scheduler
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def get_task(db: Session, task_id: int) -> Optional[BackgroundTask]:
    return db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()

def get_task_by_name(db: Session, name: str) -> Optional[BackgroundTask]:
    return db.query(BackgroundTask).filter(BackgroundTask.name == name).first()

def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False
) -> List[BackgroundTask]:
    query = db.query(BackgroundTask)
    if enabled_only:
        query = query.filter(BackgroundTask.is_enabled == True)
    return query.offset(skip).limit(limit).all()

def get_tasks_count(
    db: Session,
    enabled_only: bool = False
) -> int:
    """获取任务总数"""
    query = db.query(BackgroundTask)
    if enabled_only:
        query = query.filter(BackgroundTask.is_enabled == True)
    return query.count()

def create_task(db: Session, task: TaskCreate) -> BackgroundTask:
    db_task = BackgroundTask(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 如果任务启用，则添加到调度器
    if db_task.is_enabled:
        schedule_task(db_task)
    
    return db_task

def update_task(
    db: Session,
    task_id: int,
    task_update: TaskUpdate
) -> Optional[BackgroundTask]:
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    
    # 更新任务属性
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    
    # 如果任务启用，重新调度
    if db_task.is_enabled:
        schedule_task(db_task)
    
    return db_task

def delete_task(db: Session, task_id: int) -> bool:
    try:
        db_task = get_task(db, task_id)
        if not db_task:
            return False
        
        # 从数据库中删除任务
        db.delete(db_task)
        db.commit()
        
        # 从调度器中移除任务
        scheduler = get_scheduler()
        if scheduler and scheduler.running:
            job_id = f"task_{task_id}"
            # 先检查任务是否存在
            if scheduler.get_job(job_id):
                try:
                    scheduler.remove_job(job_id)
                    logger.info(f"任务 {task_id} 已从调度器中移除")
                except Exception as e:
                    logger.warning(f"从调度器移除任务 {task_id} 时出错: {str(e)}")
            else:
                logger.info(f"任务 {task_id} 在调度器中不存在，无需移除")
        
        return True
    except Exception as e:
        logger.error(f"删除任务 {task_id} 失败: {str(e)}", exc_info=True)
        return False 
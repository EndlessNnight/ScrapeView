import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.db.session import get_db_context
from app.models.task import BackgroundTask
from app.core.task_functions import get_task_function
from app.schemas.task import TaskType
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建调度器实例
scheduler = None

def get_scheduler() -> AsyncIOScheduler:
    """获取或创建调度器实例"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler

async def shutdown_scheduler():
    """关闭调度器"""
    global scheduler
    if scheduler and scheduler.running:
        logger.info("正在关闭调度器...")
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("调度器已关闭")

async def execute_task(task_id: int):
    """执行指定的任务"""
    with get_db_context() as db:
        try:
            # 获取任务信息
            task = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
            if not task:
                logger.error(f"任务未找到: {task_id}")
                return

            logger.info(f"准备执行任务: {task.name} (ID: {task.id}, 函数: {task.function_name})")
            
            # 更新任务状态
            task.status = "running"
            task.last_run_time = datetime.now()
            db.commit()

            try:
                # 获取任务函数
                logger.info(f"尝试获取任务函数: {task.function_name}")
                func = get_task_function(task.function_name)
                
                if func is None:
                    error_msg = f"任务函数未找到: {task.function_name}"
                    logger.error(error_msg)
                    task.status = "error"
                    task.error_message = error_msg
                    db.commit()
                    return
                
                logger.info(f"成功获取任务函数: {task.function_name} (类型: {type(func)})")
                logger.info(f"开始执行任务: {task.name} ({task.function_name})")
                
                if asyncio.iscoroutinefunction(func):
                    logger.info(f"执行异步任务: {task.function_name}")
                    await func()
                else:
                    logger.info(f"执行同步任务: {task.function_name}")
                    func()
                    
                logger.info(f"任务执行完成: {task.name}")

                # 更新任务状态为空闲
                task.status = "idle"
                task.error_message = None
            except Exception as e:
                # 记录错误信息
                error_msg = str(e)
                logger.error(f"任务执行失败 {task.name}: {error_msg}", exc_info=True)
                task.status = "error"
                task.error_message = error_msg

            # 更新任务信息
            task.last_run_time = datetime.now()
            db.commit()

        except Exception as e:
            logger.error(f"执行任务时出错 {task_id}: {str(e)}", exc_info=True)

def schedule_task(task: BackgroundTask):
    """将任务添加到调度器"""
    try:
        logger.info(f"正在调度任务: {task.name} (ID: {task.id}, 函数: {task.function_name})")
        
        # 如果是一次性任务，不添加到调度器
        if task.task_type == TaskType.ONCE.value:
            logger.info(f"任务 {task.name} 是一次性任务，不添加到调度器")
            return True
        
        # 如果是定时任务但没有cron表达式，返回失败
        if not task.cron_expression:
            logger.error(f"定时任务 {task.name} 没有设置cron表达式")
            return False
            
        # 先验证任务函数是否存在
        func = get_task_function(task.function_name)
        if func is None:
            logger.error(f"无法调度任务 {task.name}: 函数 {task.function_name} 未找到")
            return False
            
        logger.info(f"成功获取任务函数: {task.function_name}")
        
        current_scheduler = get_scheduler()
        try:
            job = current_scheduler.add_job(
                execute_task,
                CronTrigger.from_crontab(task.cron_expression),
                args=[task.id],
                id=f"task_{task.id}",
                replace_existing=True
            )
            
            logger.info(f"任务 {task.name} 添加到调度器成功")
            
            # 只有在调度器运行时才更新下次运行时间
            if current_scheduler.running:
                next_run_time = job.next_run_time
                logger.info(f"任务 {task.name} 下次运行时间: {next_run_time}")
                
                with get_db_context() as db:
                    task_db = db.query(BackgroundTask).filter(BackgroundTask.id == task.id).first()
                    if task_db:
                        task_db.next_run_time = next_run_time
                        db.commit()
                        
            logger.info(f"任务 {task.name} 调度成功")
            return True
            
        except Exception as e:
            logger.error(f"添加任务到调度器失败: {str(e)}", exc_info=True)
            return False
            
    except Exception as e:
        logger.error(f"调度任务 {task.name} 失败: {str(e)}", exc_info=True)
        return False

def init_scheduler():
    """初始化调度器，加载所有启用的任务"""
    try:
        logger.info("开始初始化调度器...")
        current_scheduler = get_scheduler()
        
        # 先启动调度器
        if not current_scheduler.running:
            current_scheduler.start()
            logger.info("调度器启动成功")
        else:
            logger.info("调度器已在运行中")
        
        with get_db_context() as db:
            tasks = db.query(BackgroundTask).filter(BackgroundTask.is_enabled == True).all()
            logger.info(f"找到 {len(tasks)} 个启用的任务")
            
            for task in tasks:
                logger.info(f"正在处理任务: {task.name} (ID: {task.id}, 函数: {task.function_name})")
                success = schedule_task(task)
                if not success:
                    logger.error(f"任务 {task.name} 调度失败")
                    
    except Exception as e:
        logger.error(f"初始化调度器失败: {str(e)}", exc_info=True)
        raise  # 重新抛出异常，这样我们能看到完整的错误堆栈

async def run_task_now(task_id: int):
    """立即运行指定任务"""
    try:
        await execute_task(task_id)
        return True
    except Exception as e:
        logger.error(f"立即执行任务失败 {task_id}: {str(e)}", exc_info=True)
        return False 
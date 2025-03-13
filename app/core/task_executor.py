import asyncio
from datetime import datetime
import logging
from typing import Dict, Any
from functools import partial
from app.db.session import get_db_context
from app.models.task import BackgroundTask
from app.core.task_functions import get_task_function
from app.core.task_context import set_task_context, clear_task_context
from app.crud.task import delete_task

logger = logging.getLogger(__name__)

# 存储正在运行的任务
running_tasks: Dict[int, asyncio.Task] = {}

def run_sync_task_with_context(func, task_params: Dict[str, Any] = None):
    """在新线程中执行同步任务，并确保任务上下文被正确设置"""
    try:
        if task_params:
            set_task_context(task_params)
        return func()
    finally:
        clear_task_context()

async def execute_task_in_background(task_id: int, task_params: Dict[str, Any] = None):
    """在后台执行任务
    
    Args:
        task_id: 任务ID
        task_params: 任务参数
    """
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
            task.error_message = None
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
                    # 删除失败的任务
                    delete_task(db, task_id)
                    return
                
                logger.info(f"成功获取任务函数: {task.function_name} (类型: {type(func)})")
                logger.info(f"开始执行任务: {task.name} ({task.function_name})")
                
                if asyncio.iscoroutinefunction(func):
                    logger.info(f"执行异步任务: {task.function_name}")
                    if task_params:
                        set_task_context(task_params)
                        await func()
                    else:
                        await func()
                else:
                    logger.info(f"执行同步任务: {task.function_name}")
                    # 使用线程池执行同步函数，并确保任务上下文被正确设置
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        partial(run_sync_task_with_context, func, task_params)
                    )
                    
                logger.info(f"任务执行完成: {task.name}")

                # 更新任务状态为空闲
                task.status = "idle"
                task.error_message = None
                db.commit()
                
                # 只有一次性任务执行完成后才删除
                if task.task_type == "once":
                    try:
                        delete_task(db, task_id)
                        logger.info(f"已删除完成的一次性任务: {task_id}")
                    except Exception as e:
                        logger.warning(f"删除已完成的一次性任务 {task_id} 时出错: {str(e)}")

            except Exception as e:
                error_msg = f"任务执行出错: {str(e)}"
                logger.error(error_msg, exc_info=True)
                task.status = "error"
                task.error_message = error_msg
                db.commit()
                # 删除失败的任务
                try:
                    delete_task(db, task_id)
                    logger.info(f"已删除失败的任务: {task_id}")
                except Exception as e:
                    logger.warning(f"删除失败任务 {task_id} 时出错: {str(e)}")
            finally:
                # 清理任务上下文
                clear_task_context()

        except Exception as e:
            logger.error(f"任务执行过程中发生错误: {str(e)}", exc_info=True)
        finally:
            # 清理运行中的任务记录
            if task_id in running_tasks:
                del running_tasks[task_id]

async def start_task(task_id: int, task_params: Dict[str, Any] = None) -> bool:
    """启动任务的异步执行
    
    Args:
        task_id: 任务ID
        task_params: 任务参数
    """
    try:
        # 检查任务是否已经在运行
        if task_id in running_tasks:
            logger.warning(f"任务 {task_id} 已经在运行中")
            return False

        # 创建异步任务
        task = asyncio.create_task(execute_task_in_background(task_id, task_params))
        running_tasks[task_id] = task
        
        return True
    except Exception as e:
        logger.error(f"启动任务 {task_id} 失败: {str(e)}", exc_info=True)
        return False

def is_task_running(task_id: int) -> bool:
    """检查任务是否正在运行"""
    return task_id in running_tasks 
from typing import Dict, Callable, Any, List
import logging
# from app.scripts.douyin import tasks as douyin_tasks
# from app.scripts.douyin.task import test_aa
from app.scripts.douyin.task import collect_creator_videos, test_task, test_task_async, collect_creator_info
import inspect

logger = logging.getLogger(__name__)

# 任务函数映射表
task_functions: Dict[str, Callable[[], Any]] = {
    # 抖音相关任务
    # "test_aa": test_aa,
    "collect_creator_videos": collect_creator_videos,
    'test_task': test_task,
    'test_task_async': test_task_async,
    'collect_creator_info': collect_creator_info
}

def get_task_function(function_name: str) -> Callable[[], Any] | None:
    """获取任务函数"""
    if function_name not in task_functions:
        logger.error(f"Task function {function_name} not found")
        return None
    return task_functions.get(function_name)

def get_available_tasks(skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """获取所有可用的任务函数信息
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    Returns:
        Dict[str, Any]: 包含总数和任务函数列表的字典：
            - total: 总数
            - items: 任务函数列表，每个任务包含：
                - name: 函数名
                - description: 函数描述（从docstring获取）
                - is_async: 是否是异步函数
    """
    available_tasks = []
    for name, func in task_functions.items():
        task_info = {
            "name": name,
            "description": inspect.getdoc(func) or "暂无描述",
            "is_async": inspect.iscoroutinefunction(func)
        }
        available_tasks.append(task_info)
    
    # 计算总数
    total = len(available_tasks)
    
    # 应用分页
    paginated_tasks = available_tasks[skip:skip + limit]
    
    return {
        "total": total,
        "items": paginated_tasks
    } 
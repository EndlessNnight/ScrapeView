from typing import Dict, Any
import contextvars
import logging

logger = logging.getLogger(__name__)

# 创建上下文变量
_task_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar('task_context', default={})

def set_task_context(context: Dict[str, Any]) -> None:
    """设置任务上下文"""
    _task_context.set(context)

def get_task_context() -> Dict[str, Any]:
    """获取任务上下文"""
    return _task_context.get()

def clear_task_context() -> None:
    """清除任务上下文"""
    _task_context.set({}) 
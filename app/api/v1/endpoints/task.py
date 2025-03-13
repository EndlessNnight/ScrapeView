from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, TaskFunctionInfo, TaskFunctionListResponse
from app.schemas.common import ApiResponse, ErrorCode
from app.crud import task as task_crud
from app.core.task_executor import start_task, is_task_running
from app.core.task_functions import get_available_tasks
from app.db.session import get_db
from app.core.security import get_current_user

router = APIRouter()

@router.get("/tasks", response_model=ApiResponse[TaskListResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取后台任务列表"""
    try:
        total = task_crud.get_tasks_count(db, enabled_only=enabled_only)
        tasks = task_crud.get_tasks(db, skip=skip, limit=limit, enabled_only=enabled_only)
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="获取任务列表成功",
            data=TaskListResponse(
                total=total,
                items=tasks
            )
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=f"获取任务列表失败: {str(e)}"
        )

@router.post("/tasks", response_model=ApiResponse[TaskResponse])
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建新任务"""
    try:
        db_task = task_crud.get_task_by_name(db, name=task.name)
        if db_task:
            return ApiResponse(
                code=ErrorCode.PARAM_ERROR,
                message="任务名称已存在"
            )
        
        task = task_crud.create_task(db=db, task=task)
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="创建任务成功",
            data=task
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=f"创建任务失败: {str(e)}"
        )

@router.get("/tasks/functions", response_model=ApiResponse[TaskFunctionListResponse])
async def list_task_functions(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """获取所有可用的任务函数列表
    
    Args:
        skip: 跳过的记录数，用于分页
        limit: 每页记录数
    """
    try:
        result = get_available_tasks(skip=skip, limit=limit)
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="获取任务函数列表成功",
            data=TaskFunctionListResponse(**result)
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=f"获取任务函数列表失败: {str(e)}"
        )

@router.get("/tasks/{task_id}", response_model=ApiResponse[TaskResponse])
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取指定任务详情"""
    try:
        db_task = task_crud.get_task(db, task_id=task_id)
        if db_task is None:
            return ApiResponse(
                code=ErrorCode.NOT_FOUND,
                message="任务不存在"
            )
            
        # 检查任务是否正在运行
        if is_task_running(task_id):
            db_task.status = "running"
            
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="获取任务成功",
            data=db_task
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=f"获取任务失败: {str(e)}"
        )

@router.put("/tasks/{task_id}", response_model=ApiResponse[TaskResponse])
async def update_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新任务"""
    try:
        db_task = task_crud.update_task(db=db, task_id=task_id, task_update=task)
        if db_task is None:
            return ApiResponse(
                code=ErrorCode.NOT_FOUND,
                message="任务不存在"
            )
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="更新任务成功",
            data=db_task
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=f"更新任务失败: {str(e)}"
        )

@router.delete("/tasks/{task_id}", response_model=ApiResponse)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除任务"""
    try:
        success = task_crud.delete_task(db=db, task_id=task_id)
        if not success:
            return ApiResponse(
                code=ErrorCode.NOT_FOUND,
                message="任务不存在"
            )
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="删除任务成功"
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=f"删除任务失败: {str(e)}"
        )

@router.post("/tasks/{task_id}/run", response_model=ApiResponse)
async def run_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """立即运行指定任务"""
    try:
        db_task = task_crud.get_task(db, task_id=task_id)
        if db_task is None:
            return ApiResponse(
                code=ErrorCode.NOT_FOUND,
                message="任务不存在"
            )
        
        # 检查任务是否已在运行
        if is_task_running(task_id):
            return ApiResponse(
                code=ErrorCode.PARAM_ERROR,
                message="任务正在运行中"
            )
        
        task_params = {
            'user_id': current_user.id
        }
        # 启动后台任务
        success = await start_task(task_id, task_params)
        if not success:
            return ApiResponse(
                code=ErrorCode.SYSTEM_ERROR,
                message="启动任务失败"
            )
        
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="任务已开始执行"
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=f"启动任务失败: {str(e)}"
        ) 
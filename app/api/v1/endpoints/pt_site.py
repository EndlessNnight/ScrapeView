from fastapi import APIRouter, HTTPException, Depends, Query, Path as PathParam, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.schemas.pt_site import (
    ApiResponse,
    PaginationResponse,
    TorrentListResponse,
    TorrentDetailResponse,
    PTSitesResponse,
    Site,
    SiteCreate,
    SiteUpdate,
    SiteWithUsers,
    SupportedSite,
    PTUserResponse,
    CategoryResponse
)
from app.scripts.pt_site.dispatch import dispatch, get_all_sites, get_site_name, get_site_set_params
from typing import List, Optional, Any, Dict, Tuple
from app.core.error_codes import ErrorCode
from app.core.cache import LocalCache
from app.core.config import settings
import app.crud.pt_site as crud
import tempfile
import os
import logging
# 获取日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()


def get_pter_instance(db: Session, site_id: int, user_id: int) -> Tuple[Any, Any]:
    """
    获取站点并创建pter实例
    
    Args:
        db: 数据库会话
        site_id: 站点ID
        user_id: 用户ID
        
    Returns:
        Tuple[Site, Any]: 站点对象和pter实例
        
    Raises:
        HTTPException: 站点不存在或无权访问
    """
    site = crud.get_site_by_id(db, site_id, user_id=user_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="站点不存在或无权访问"
        )
    
    pter = dispatch(
        site.schema_type, 
        cookie=site.cookie, 
        user_agent=site.user_agent, 
        api_key=site.api_key, 
        auth_token=site.auth_token, 
        passkey=site.passkey
    )
    
    return site, pter


@router.get("/ptsites", response_model=ApiResponse[PaginationResponse[PTSitesResponse]])
async def get_pt_sites(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取当前用户的所有PT站点列表及其用户数据"""
    try:
        # 获取用户的所有站点
        sites = crud.get_sites(db, current_user.id, skip=skip, limit=limit, include_user=True)
        total = crud.get_sites_count(db, current_user.id)
        
        # 构建响应数据
        items = []
        for site in sites:
            # 获取站点的PT用户数据
            pt_users = crud.get_site_users(db, site.id)
            
            # 如果站点有PT用户数据，使用第一个用户的数据
            pt_user = pt_users[0] if pt_users else None
            
            pter = dispatch(site.schema_type, cookie=site.cookie, user_agent=site.user_agent, api_key=site.api_key, auth_token=site.auth_token, passkey=site.passkey)
            category_list = pter.get_all_category()
            category = [CategoryResponse(id=cat.id, name=cat.name) for cat in category_list]

            # 构建响应项
            site_response = PTSitesResponse(
                id=site.id,
                name=site.name,
                type=site.schema_type,
                category=category, 
                share_rate=pt_user.ratio if pt_user and pt_user.ratio else 0.0,
                upload=pt_user.uploaded if pt_user and pt_user.uploaded else 0.0,
                download=pt_user.downloaded if pt_user and pt_user.downloaded else 0.0,
                username=pt_user.username if pt_user else "",
                seed=pt_user.current_upload if pt_user and pt_user.current_upload else 0.0,  # 暂无做种数据
                time_magic=pt_user.bonus if pt_user and pt_user.bonus else 0.0
            )
            items.append(site_response)
        
        # 返回分页响应
        return ApiResponse(
            code=200,
            message="获取PT站点列表成功",
            data=PaginationResponse(
                items=items,
                total=total
            )
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取PT站点列表失败: {str(e)}",
            data=None
        )


@router.get("/torrents", response_model=ApiResponse[PaginationResponse[TorrentListResponse]])
async def get_torrents(
    site_id: int = Query(..., description="站点ID"),
    page: int = Query(0, ge=0),
    cat_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取种子列表
    
    Args:
        page: 页码，从0开始
        cat_id: 分类ID，不传则使用默认分类
    """
    try:
        # 获取站点和pter实例
        site, pter = get_pter_instance(db, site_id, current_user.id)
        
        params = {"page": page}
        if cat_id:
            params["cat_id"] = cat_id
        
        # cache = LocalCache()
        # cache_key = f"get_torrents_{site_id}_{page}_{cat_ids}"
        # torrents = cache.get(cache_key)
        # if not torrents:
            # torrents = pter.get_torrents(**params)
            # cache.set(cache_key, torrents)
        if site.schema_type == "mteam":
            torrents = pter.get_torrents(cat_id=cat_id)
        else:
            torrents = pter.get_torrents(**params)
        # 由于PTer API不返回总数，这里暂时将总数设置为当前页的种子数
        total = len(torrents.torrents)
        
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="获取种子列表成功",
            data=PaginationResponse(
                items=torrents.torrents,
                total=total
            )
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取种子列表失败: {str(e)}",
            data=None
        )


@router.get("/torrents/search", response_model=ApiResponse[PaginationResponse[TorrentListResponse]])
async def search_torrents(
    site_id: int = Query(..., description="站点ID"),
    keyword: str = Query(..., description="搜索关键词"),
    cat_id: int = Query(None, description="分类ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """搜索种子
    
    Args:
        keyword: 搜索关键词
        cat_id: 分类ID，不传则使用默认分类
    """
    try:
        # 获取站点和pter实例
        _, pter = get_pter_instance(db, site_id, current_user.id)
        
        # 搜索种子
        torrents = pter.get_search(keyword)
        # 由于PTer API不返回总数，这里暂时将总数设置为搜索结果的种子数
        total = len(torrents.torrents)
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="搜索种子成功",
            data=PaginationResponse(
                items=torrents.torrents,
                total=total
            )
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"搜索种子失败: {str(e)}",
            data=None
        )


@router.get("/torrents/{torrent_id}/download", response_model=ApiResponse[bytes])
async def get_torrent_files(
    torrent_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取种子文件列表"""

    # 定义删除文件的函数
    def remove_file(path: str):
        try:
            if os.path.exists(path):
                os.unlink(path)
        except Exception as e:
            print(f"删除临时文件失败: {str(e)}")
    
    # 创建临时文件
    temp_file = None
    temp_file_path = ""
    
    try:
        # 获取站点和pter实例
        _, pter = get_pter_instance(db, site_id, current_user.id)
        
        torrent_content = pter.get_torrent_files(torrent_id)
        
        # 使用NamedTemporaryFile创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".torrent")
        temp_file_path = temp_file.name
        
        # 写入二进制内容并关闭文件
        temp_file.write(torrent_content)
        temp_file.close()
        
        # 返回文件响应
        return FileResponse(
            path=temp_file_path, 
            media_type='application/octet-stream', 
            filename=f'{torrent_id}.torrent',
            background=BackgroundTask(remove_file, temp_file_path)  # 响应发送后删除临时文件
        )
    except Exception as e:
        # 如果出现异常，确保删除临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass
        return ApiResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取种子文件列表失败: {str(e)}",
            data=None
        )


@router.get("/torrents/{torrent_id}", response_model=ApiResponse[TorrentDetailResponse])
async def get_torrent_detail(
    site_id: int,
    torrent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取种子详情
    
    Args:
        torrent_id: 种子ID
    """
    try:
        # 获取站点和pter实例
        site, pter = get_pter_instance(db, site_id, current_user.id)
        
        cache = LocalCache()
        cache_key = f"get_torrent_detail{site_id}_{torrent_id}"
        details = cache.get(cache_key)
        # 获取种子详情
        if not details:
            details = pter.get_details(torrent_id)
            cache.set(cache_key, details)
        
        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="获取种子详情成功",
            data=details
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取种子详情失败: {str(e)}",
            data=None
        )

# 站点管理API

@router.get("/sites", response_model=ApiResponse[PaginationResponse[Site]])
async def get_sites(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    获取当前用户的所有站点
    """
    sites = crud.get_sites(db, user_id=current_user.id, skip=skip, limit=limit)
    total = crud.get_sites_count(db, user_id=current_user.id)
    
    return ApiResponse(
        code=200,
        message="获取站点列表成功",
        data=PaginationResponse(
            items=sites,
            total=total
        )
    )

@router.post("/sites", response_model=ApiResponse[Site], status_code=status.HTTP_200_OK)
async def create_site(
    site: SiteCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    创建新站点
    只需要传入 schema_type, cookie 和 User-Agent（可选）
    可选参数：api_key, auth_token, passkey
    只有在成功获取到用户信息时才会创建站点
    """
    # 检查该用户是否已有相同类型的站点
    db_site = crud.get_site_by_schema_type(db, site.schema_type, user_id=current_user.id)
    if db_site:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该类型的站点已存在"
        )
    
    # 先验证能否获取用户信息
    try:
        # 创建PTer实例并获取用户信息
        pter = dispatch(
            site.schema_type, 
            cookie=site.cookie, 
            user_agent=site.user_agent, 
            api_key=site.api_key, 
            auth_token=site.auth_token, 
            passkey=site.passkey
        )

        user_info = pter.get_user_info()
        
        # 如果没有获取到用户信息，则不创建站点
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取用户信息，请检查cookie是否有效"
            )
        
        # 获取站点名称
        site_name = get_site_name(site.schema_type)
        # 创建站点，直接传入站点名称
        db_site = crud.create_site(db, site, user_id=current_user.id, site_name=site_name)
        
        # 创建站点用户关联
        crud.create_site_user(db, db_site.id, user_info)
        
        # 构建响应数据
        item = Site(
            id=db_site.id,
            name=site_name,
            url=db_site.url,
            schema_type=db_site.schema_type,
            api_key=db_site.api_key,
            auth_token=db_site.auth_token,
            passkey=db_site.passkey,
            user_info=user_info
        )
        return ApiResponse(
            code=200,
            message="创建站点成功",
            data=item
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建站点失败: {str(e)}"
        )

@router.get("/sites/{site_id}", response_model=ApiResponse[Site])
async def get_site(
    site_id: int = PathParam(..., ge=1, description="站点ID"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    获取指定站点详情
    """
    db_site = crud.get_site_by_id(db, site_id, user_id=current_user.id)
    if not db_site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="站点不存在或无权访问"
        )
    
    return ApiResponse(
        code=200,
        message="获取站点详情成功",
        data=db_site
    )

@router.put("/sites/{site_id}", response_model=ApiResponse[Site])
async def update_site(
    site_id: int = PathParam(..., ge=1, description="站点ID"),
    site_update: SiteUpdate = ...,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    更新站点信息
    可以修改 cookie、User-Agent、api_key、auth_token 和 passkey
    """
    # 检查站点是否存在
    db_site = crud.get_site_by_id(db, site_id, user_id=current_user.id)
    if not db_site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="站点不存在或无权访问"
        )
    
    # 更新站点
    updated_site = crud.update_site(db, site_id, site_update, user_id=current_user.id)
    
    # 如果更新了 cookie，尝试获取最新的用户信息
    if site_update.cookie:
        try:
            # 创建新的pter实例，使用更新后的站点信息
            pter = dispatch(
                updated_site.schema_type, 
                cookie=site_update.cookie, 
                user_agent=site_update.user_agent or updated_site.user_agent, 
                api_key=site_update.api_key or updated_site.api_key, 
                auth_token=site_update.auth_token or updated_site.auth_token,
                passkey=site_update.passkey or updated_site.passkey
            )

            # 获取用户信息
            user_info = pter.get_user_info()
            if user_info:
                # 更新用户信息
                pt_users = crud.get_site_users(db, site_id)
                if pt_users:
                    # 更新第一个用户
                    crud.update_site_user(db, pt_users[0].id, user_info)
        except Exception as e:
            # 记录错误但不影响更新结果
            print(f"更新用户信息时出错: {str(e)}")
    
    return ApiResponse(
        code=200,
        message="更新站点成功",
        data=updated_site
    )

@router.delete("/sites/{site_id}", response_model=ApiResponse[None])
async def delete_site(
    site_id: int = PathParam(..., ge=1, description="站点ID"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    删除站点
    """
    # 检查站点是否存在
    db_site = crud.get_site_by_id(db, site_id, user_id=current_user.id)
    if not db_site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="站点不存在或无权访问"
        )
    
    # 删除站点
    result = crud.delete_site(db, site_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除站点失败"
        )
    
    return ApiResponse(
        code=200,
        message="删除站点成功",
        data=None
    )

@router.get("/sites/{site_id}/users", response_model=ApiResponse[SiteWithUsers])
async def get_site_with_users(
    site_id: int = PathParam(..., ge=1, description="站点ID"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    获取站点及其用户信息
    """
    site = crud.get_site_with_users(db, site_id, user_id=current_user.id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="站点不存在或无权访问"
        )
    
    return ApiResponse(
        code=200,
        message="获取站点及用户信息成功",
        data=site
    )

@router.get("/supported-sites", response_model=ApiResponse[List[SupportedSite]])
async def get_supported_sites():
    """
    获取当前所支持的站点列表
    返回站点名称和类型
    """
    sites = get_all_sites()
    return ApiResponse(
        code=200,
        message="获取支持的站点列表成功",
        data=sites
    )

@router.post("/sites/{site_id}/refresh-user", response_model=ApiResponse[PTUserResponse])
async def refresh_site_user_info(
    site_id: int = PathParam(..., ge=1, description="站点ID"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    更新指定站点的用户信息
    
    通过站点ID获取站点信息，然后使用站点的cookie和user-agent获取最新的用户信息，并更新数据库中的用户数据
    """
    try:
        # 获取站点和pter实例
        site, pter = get_pter_instance(db, site_id, current_user.id)
        
        user_info = pter.get_user_info()
        
        # 如果没有获取到用户信息，则返回错误
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取用户信息，请检查cookie是否有效"
            )
        
        # 获取站点用户
        pt_users = crud.get_site_users(db, site_id)
        if not pt_users or len(pt_users) == 0:
            # 如果没有用户，则创建新用户
            pt_user = crud.create_site_user(db, site_id, user_info)
        else:
            # 更新第一个用户（通常只有一个用户）
            pt_user = crud.update_site_user(db, pt_users[0].id, user_info)
        
        return {
            "code": 200,
            "message": "用户信息更新成功",
            "data": pt_user
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息失败: {str(e)}"
        )

@router.get("/sites/{site_id}/categories", response_model=ApiResponse[List[CategoryResponse]])
async def get_site_categories(
    site_id: int = PathParam(..., ge=1, description="站点ID"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    获取指定站点的分类信息
    
    返回站点所有分类的ID和名称
    """
    try:
        # 获取站点和pter实例
        _, pter = get_pter_instance(db, site_id, current_user.id)
        
        # 获取分类信息
        category_list = pter.get_all_category()
        
        return ApiResponse(
            code=200,
            message="获取站点分类成功",
            data=category_list
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取站点分类失败: {str(e)}"
        )

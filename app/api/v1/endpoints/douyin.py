from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session
from app.schemas.douyin import (
    DouyinCookieSchema, 
    DouyinCookieResponse, 
    DouyinCreatorCreate, 
    DouyinCreatorResponse,
    DouyinVideoResponse,
    ApiResponse,
    PaginationResponse,
    DouyinImagePostResponse,
    DouyinContentResponse,
    DouyinFollowing,
    DouyinFollowingListResponse,
    DouyinCreatorAddRequest,
    DouyinCreatorUpdate,
    DouyinContentListResponse
)
from app.services.douyin import save_douyin_cookie, get_douyin_cookie
from app.db.session import get_db
from app.core.task_executor import start_task

from typing import Optional, List
from ....models.douyin import DouyinCreator, DouyinContent, DouyinContentFile
from ....scripts.douyin.tiktok_api import TikTokApi
from app.core.security import get_current_user
from app.core.error_codes import ErrorCode
from datetime import datetime
from app.schemas.task import TaskType, TaskCreate
from sqlalchemy import desc
from fastapi.responses import StreamingResponse
import os

import re

router = APIRouter()

@router.post("/creators", response_model=ApiResponse[DouyinCreatorResponse])
async def add_douyin_creator(
    creator_data: DouyinCreatorAddRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """通过分享链接添加抖音创作者"""
    try:
        # 处理分享链接,只保留URL部分
        share_url = creator_data.share_url
        if "douyin.com" in share_url:
            # 使用正则提取URL
            url_pattern = r'https://v\.douyin\.com/[a-zA-Z0-9]+/'
            match = re.search(url_pattern, share_url)
            if match:
                share_url = match.group(0)

        saved_cookie = get_douyin_cookie(db, current_user.id)
        tiktok_api = TikTokApi(cookie=saved_cookie)

        # 从分享URL获取sec_user_id
        sec_user_id = tiktok_api.get_sec_user_id(share_url)
        if not sec_user_id:
            return ApiResponse(code=400, message="无法从分享链接获取用户ID", data=None)
            
        # 检查创作者是否已存在
        existing_creator = db.query(DouyinCreator).filter(
            DouyinCreator.sec_user_id == sec_user_id
        ).first()
        
        if existing_creator:
            return ApiResponse(code=400, message="该创作者已存在", data=None)
            
        # 获取用户信息
        user_info = tiktok_api.get_user_info(sec_user_id)
        # print("user_info", user_info)
        if not user_info:
            return ApiResponse(code=400, message="无法获取创作者信息", data=None)
            
        # 处理ip_location数据
        ip_location = getattr(user_info.user, 'ip_location', None)
        if ip_location and "IP属地：" in ip_location:
            ip_location = ip_location.split("IP属地：")[1]

        # 创建新的创作者记录
        creator_model = DouyinCreatorCreate(
            sec_user_id=sec_user_id,
            nickname=user_info.user.nickname,
            avatar_url=user_info.user.avatar_larger.url_list[0],
            unique_id=user_info.user.unique_id,
            signature=user_info.user.signature,
            ip_location=ip_location,
            gender=getattr(user_info.user, 'gender', None),
            follower_count=user_info.user.follower_count,
            following_count=getattr(user_info.user, 'following_count', None),
            aweme_count=getattr(user_info.user, 'aweme_count', None),
            total_favorited=user_info.user.total_favorited,
            status=1,  # 1表示正常状态
            auto_update=creator_data.auto_update,
            download_video=creator_data.download_video,
            download_cover=creator_data.download_cover
        )
        # print("creator_data", creator_data)
        new_creator = DouyinCreator(**creator_model.model_dump())
        db.add(new_creator)
        db.commit()
        db.refresh(new_creator)
        
        return ApiResponse(
            code=200,
            message="创作者添加成功",
            data=new_creator
        )
        
    except Exception as e:
        return ApiResponse(code=500, message=f"添加创作者失败: {str(e)}", data=None)

@router.get("/creators", response_model=ApiResponse[PaginationResponse[DouyinCreatorResponse]])
async def get_creators(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取已添加的抖音创作者列表"""
    creators = db.query(DouyinCreator).order_by(DouyinCreator.created_at.desc()).offset(skip).limit(limit).all()
    total = db.query(DouyinCreator).count()
    
    pagination_data = PaginationResponse(
        items=creators,
        total=total
    )
    
    return ApiResponse(
        code=200,
        message="获取创作者列表成功",
        data=pagination_data
    )

@router.get("/creators/search", response_model=ApiResponse[PaginationResponse[DouyinCreatorResponse]])
async def search_creators(
    nickname: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """通过昵称模糊查询创作者信息"""
    query = db.query(DouyinCreator).filter(
        DouyinCreator.nickname.like(f"%{nickname}%")
    ).order_by(DouyinCreator.created_at.desc())
    
    creators = query.offset(skip).limit(limit).all()
    total = query.count()
    
    pagination_data = PaginationResponse(
        items=creators,
        total=total
    )
    
    return ApiResponse(
        code=200,
        message="查询创作者列表成功",
        data=pagination_data
    )

@router.get("/creators/{creator_id}", response_model=ApiResponse[DouyinCreatorResponse])
async def get_creator(
    creator_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取指定抖音创作者信息"""
    creator = db.query(DouyinCreator).filter(DouyinCreator.id == creator_id).first()
    if not creator:
        return ApiResponse(code=404, message="创作者不存在", data=None)
    return ApiResponse(code=200, message="获取创作者信息成功", data=creator)

@router.put("/creators/{creator_id}", response_model=ApiResponse[DouyinCreatorResponse])
async def update_creator(
    creator_id: int,
    creator_data: DouyinCreatorUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """修改抖音创作者信息"""
    creator = db.query(DouyinCreator).filter(DouyinCreator.id == creator_id).first()
    if not creator:
        return ApiResponse(code=404, message="创作者不存在", data=None)
    
    for field, value in creator_data.model_dump(exclude_unset=True).items():
        setattr(creator, field, value)
    
    db.commit()
    db.refresh(creator)
    return ApiResponse(code=200, message="更新创作者信息成功", data=creator)

@router.delete("/creators/{creator_id}", response_model=ApiResponse[dict])
async def delete_creator(
    creator_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除抖音创作者"""
    creator = db.query(DouyinCreator).filter(DouyinCreator.id == creator_id).first()
    if not creator:
        return ApiResponse(code=404, message="创作者不存在", data=None)
    
    db.delete(creator)
    db.commit()
    
    return ApiResponse(
        code=200,
        message="创作者已成功删除",
        data={"id": creator_id}
    )

@router.post("/creators/{creator_id}/refresh", response_model=ApiResponse[DouyinCreatorResponse])
async def refresh_creator(
    creator_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新抖音创作者信息"""
    try:
        # 获取创作者信息
        creator = db.query(DouyinCreator).filter(DouyinCreator.id == creator_id).first()
        if not creator:
            return ApiResponse(code=404, message="创作者不存在", data=None)

        # 使用抖音API获取最新信息
        saved_cookie = get_douyin_cookie(db, current_user.id)
        tiktok_api = TikTokApi(cookie=saved_cookie)
        user_info = tiktok_api.get_user_info(creator.sec_user_id)
        
        if not user_info:
            return ApiResponse(code=400, message="无法获取创作者最新信息", data=None)
        
        # 处理ip_location数据
        ip_location = getattr(user_info.user, 'ip_location', None)
        if ip_location and "IP属地：" in ip_location:
            ip_location = ip_location.split("IP属地：")[1]
            
        # 更新创作者信息
        creator.nickname = user_info.user.nickname
        creator.avatar_url = user_info.user.avatar_larger.url_list[0]
        creator.unique_id = user_info.user.unique_id
        creator.signature = user_info.user.signature
        creator.ip_location = ip_location
        creator.gender = getattr(user_info.user, 'gender', None)
        creator.follower_count = user_info.user.follower_count
        creator.following_count = getattr(user_info.user, 'following_count', None)
        creator.aweme_count = getattr(user_info.user, 'aweme_count', None)
        creator.total_favorited = user_info.user.total_favorited
        
        db.commit()
        db.refresh(creator)
        
        return ApiResponse(
            code=200,
            message="创作者信息更新成功",
            data=creator
        )
        
    except Exception as e:
        return ApiResponse(code=500, message=f"更新创作者信息失败: {str(e)}", data=None)

@router.post("/creators/{sec_user_id}/collect-videos", response_model=ApiResponse)
async def collect_creator_videos_api(
    sec_user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """立即执行创作者视频采集任务"""
    try:
        # 检查创作者是否存在
        creator = db.query(DouyinCreator).filter(
            DouyinCreator.sec_user_id == sec_user_id
        ).first()
        
        if not creator:
            return ApiResponse(
                code=ErrorCode.NOT_FOUND,
                message="创作者不存在"
            )
            
        # 创建临时任务
        from app.crud.task import create_task
        
        task_name = f"collect_videos_{creator.nickname}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        task = TaskCreate(
            name=task_name,
            function_name="collect_creator_videos",
            task_type=TaskType.ONCE,  # 使用枚举值
            description=f"采集创作者 {creator.nickname} 的视频数据",
            is_enabled=True
        )
        
        try:
            # 创建并执行任务
            db_task = create_task(db, task)
            if not db_task:
                return ApiResponse(
                    code=ErrorCode.SYSTEM_ERROR,
                    message="创建任务失败"
                )
                        
            success = await start_task(db_task.id, {
                "sec_user_id": sec_user_id,
                "user_id": current_user.id
            })
            
            if not success:
                # 如果启动失败，删除任务
                from app.crud.task import delete_task
                delete_task(db, db_task.id)
                return ApiResponse(
                    code=ErrorCode.SYSTEM_ERROR,
                    message="启动任务失败"
                )
            
            return ApiResponse(
                code=ErrorCode.SUCCESS,
                message="视频采集任务已开始执行",
                data={"task_id": db_task.id}
            )
            
        except Exception as e:
            return ApiResponse(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"任务执行失败: {str(e)}"
            )
        
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=f"执行视频采集任务失败: {str(e)}"
        )

@router.get("/creators/{sec_user_id}/videos", response_model=ApiResponse[PaginationResponse[DouyinVideoResponse]])
async def get_creator_videos(
    sec_user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("aweme_id", description="排序字段: aweme_id, created_at, play_count, digg_count, collect_count, share_count"),
    sort_desc: bool = Query(True, description="是否降序排序"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取创作者的视频列表
    
    Args:
        sec_user_id: 创作者的sec_user_id
        skip: 跳过的记录数
        limit: 返回的记录数
        sort_by: 排序字段
        sort_desc: 是否降序排序
    """
    try:
        # 检查创作者是否存在
        creator = db.query(DouyinCreator).filter(
            DouyinCreator.sec_user_id == sec_user_id
        ).first()
        
        if not creator:
            return ApiResponse(
                code=ErrorCode.NOT_FOUND,
                message="创作者不存在"
            )
            
        # 构建查询
        query = db.query(DouyinContent).filter(
            DouyinContent.creator_id == creator.id,
            DouyinContent.content_type == "video"
        )
        
        # 默认按照is_top降序排序（置顶视频在前）
        query = query.order_by(desc(DouyinContent.is_top))
        
        # 添加排序
        sort_field = getattr(DouyinContent, sort_by, DouyinContent.aweme_id)
        if sort_desc:
            query = query.order_by(desc(DouyinContent.is_top), desc(sort_field))
        else:
            query = query.order_by(desc(DouyinContent.is_top), sort_field)
        
        # 获取总记录数
        total = query.count()
        
        # 获取分页数据
        videos = query.offset(skip).limit(limit).all()
        
        return ApiResponse(
            code=200,
            message="获取视频列表成功",
            data=PaginationResponse(
                items=videos,
                total=total
            )
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取视频列表失败: {str(e)}"
        )

@router.get("/videos/{aweme_id}/play", response_class=StreamingResponse)
async def play_video(
    aweme_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """播放视频，支持范围请求"""
    try:
        # 查询视频文件记录
        video_file = db.query(DouyinContentFile).filter(
            DouyinContentFile.aweme_id == aweme_id,
            DouyinContentFile.file_type == "video"
        ).first()
        
        if not video_file or not video_file.file_path:
            raise HTTPException(status_code=404, detail="视频文件不存在")
        
        video_path = video_file.file_path
        
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="视频文件不存在")

        file_size = os.path.getsize(video_path)
        range_header = request.headers.get("range")

        # 处理范围请求
        if range_header:
            start_byte = 0
            end_byte = file_size - 1

            if range_header.startswith("bytes="):
                range_data = range_header.replace("bytes=", "").split("-")
                if len(range_data) == 2:
                    if range_data[0]:
                        start_byte = int(range_data[0])
                    if range_data[1]:
                        end_byte = int(range_data[1])

            chunk_size = end_byte - start_byte + 1

            def iterfile():
                with open(video_path, "rb") as f:
                    f.seek(start_byte)
                    remaining = chunk_size
                    while remaining > 0:
                        chunk = f.read(min(8192, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            headers = {
                "Content-Range": f"bytes {start_byte}-{end_byte}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": "video/mp4",
            }

            return StreamingResponse(
                iterfile(),
                status_code=206,
                headers=headers
            )
        else:
            # 如果没有范围请求，返回完整文件
            def iterfile():
                with open(video_path, "rb") as f:
                    while chunk := f.read(8192):
                        yield chunk

            headers = {
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Content-Type": "video/mp4",
            }

            return StreamingResponse(
                iterfile(),
                headers=headers
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"播放视频失败: {str(e)}")

@router.get("/videos/{aweme_id}/cover", response_class=StreamingResponse)
async def get_video_cover(
    aweme_id: str,
    db: Session = Depends(get_db),
):
    """获取视频封面"""
    try:
        # 查询视频封面文件记录
        cover_file = db.query(DouyinContentFile).filter(
            DouyinContentFile.aweme_id == aweme_id,
            DouyinContentFile.file_type == "cover"
        ).first()
        
        if not cover_file or not cover_file.file_path:
            raise HTTPException(status_code=404, detail="封面文件不存在")
        
        cover_path = cover_file.file_path
        
        if not os.path.exists(cover_path):
            raise HTTPException(status_code=404, detail="封面文件不存在")
        
        def iterfile():
            with open(cover_path, "rb") as f:
                yield from f
        
        return StreamingResponse(iterfile(), media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取封面失败: {str(e)}")

@router.get("/creators/{sec_user_id}/image-posts", response_model=ApiResponse[PaginationResponse[DouyinImagePostResponse]])
async def get_creator_image_posts(
    sec_user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("aweme_id", description="排序字段: aweme_id, created_at, digg_count, collect_count, share_count"),
    sort_desc: bool = Query(True, description="是否降序排序"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取创作者的图集列表"""
    try:
        # 检查创作者是否存在
        creator = db.query(DouyinCreator).filter(
            DouyinCreator.sec_user_id == sec_user_id
        ).first()
        
        if not creator:
            return ApiResponse(
                code=ErrorCode.NOT_FOUND,
                message="创作者不存在"
            )
            
        # 构建查询
        query = db.query(DouyinContent).filter(
            DouyinContent.creator_id == creator.id,
            DouyinContent.content_type == "image"
        )
        
        # 默认按照is_top降序排序（置顶图集在前）
        query = query.order_by(desc(DouyinContent.is_top))
        
        # 添加排序
        sort_field = getattr(DouyinContent, sort_by, DouyinContent.aweme_id)
        if sort_desc:
            query = query.order_by(desc(DouyinContent.is_top), desc(sort_field))
        else:
            query = query.order_by(desc(DouyinContent.is_top), sort_field)
        
        # 获取总记录数
        total = query.count()
        
        # 获取分页数据
        image_posts = query.offset(skip).limit(limit).all()
        
        return ApiResponse(
            code=200,
            message="获取图集列表成功",
            data=PaginationResponse(
                items=image_posts,
                total=total
            )
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取图集列表失败: {str(e)}"
        )

@router.get("/image-posts/{aweme_id}", response_model=ApiResponse[DouyinImagePostResponse])
async def get_image_post_detail(
    aweme_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取图集详情"""
    try:
        # 查询图集记录
        image_post = db.query(DouyinContent).filter(
            DouyinContent.aweme_id == aweme_id,
            DouyinContent.content_type == "image"
        ).first()
        
        if not image_post:
            return ApiResponse(
                code=ErrorCode.NOT_FOUND,
                message="图集不存在"
            )
        
        return ApiResponse(
            code=200,
            message="获取图集详情成功",
            data=image_post
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取图集详情失败: {str(e)}"
        )

@router.get("/image-posts/{aweme_id}/images/{image_index}", response_class=StreamingResponse)
async def get_image_file(
    aweme_id: str,
    image_index: int,
    db: Session = Depends(get_db),
):
    """获取图集中的图片"""
    try:
        # 查询图片文件记录
        image_file = db.query(DouyinContentFile).filter(
            DouyinContentFile.aweme_id == aweme_id,
            DouyinContentFile.file_type == "image",
            DouyinContentFile.file_index == image_index
        ).first()
        
        if not image_file or not image_file.file_path:
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        image_path = image_file.file_path
        
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        def iterfile():
            with open(image_path, "rb") as f:
                yield from f
        
        return StreamingResponse(iterfile(), media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")

@router.get("/following-list", response_model=ApiResponse[DouyinFollowingListResponse])
async def get_following_list(
    count: int = 50,
    max_time: int = 0,
    min_time: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取抖音关注列表数据"""
    try:
        saved_cookie = get_douyin_cookie(db, current_user.id)
        if not saved_cookie:
            return ApiResponse(code=400, message="未找到保存的Cookie", data=None)
            
        tiktok_api = TikTokApi(cookie=saved_cookie)
        following_list = tiktok_api.get_me_following_list(count=count, max_time=max_time, min_time=min_time)
        
        if not following_list or not following_list.followings:
            return ApiResponse(code=404, message="未找到关注列表数据", data=None)
        
        # 获取所有已添加的创作者的sec_user_id列表
        existing_creators = {
            creator.sec_user_id: creator 
            for creator in db.query(DouyinCreator.sec_user_id, DouyinCreator.id).all()
        }
        
        # 提取关注列表数据,排除自己
        followings = [
            DouyinFollowing(
                nickname=item.nickname,
                sec_uid=item.sec_uid,
                uid=item.uid,
                unique_id=item.unique_id,
                signature=item.signature,
                avatar_thumb=item.avatar_thumb.url_list[0] if item.avatar_thumb and item.avatar_thumb.url_list else None,
                follow_status=item.follow_status,
                follower_status=item.follower_status,
                custom_verify=item.custom_verify,
                is_creator=item.sec_uid in existing_creators,
                creator_id=existing_creators[item.sec_uid].id if item.sec_uid in existing_creators else None
            )
            for item in following_list.followings
            if item.sec_uid != following_list.owner_sec_uid
        ]
        
        # 构建响应数据
        result = DouyinFollowingListResponse(
            followings=followings,
            has_more=following_list.has_more,
            max_time=following_list.max_time,
            min_time=following_list.min_time,
            next_req_count=following_list.next_req_count,
            owner_sec_uid=following_list.owner_sec_uid
        )
        
        return ApiResponse(
            code=200,
            message="获取关注列表成功",
            data=result
        )
        
    except Exception as e:
        return ApiResponse(code=500, message=f"获取关注列表失败: {str(e)}", data=None)

@router.post("/creators/add", response_model=ApiResponse[DouyinCreatorResponse])
async def add_douyin_creator_legacy(
    share_url: str,
    auto_update: int = 1,
    download_video: int = 1,
    download_cover: int = 1,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """通过分享链接添加抖音创作者（兼容旧版本）"""
    # 创建请求数据对象
    creator_data = DouyinCreatorAddRequest(
        share_url=share_url,
        auto_update=auto_update,
        download_video=download_video,
        download_cover=download_cover
    )
    
    # 调用新的接口实现
    return await add_douyin_creator(creator_data, db, current_user)

@router.get("/creators/{creator_id}/contents", response_model=ApiResponse[PaginationResponse[DouyinContentListResponse]])
async def get_creator_contents(
    creator_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    content_type: Optional[str] = Query(None, description="内容类型筛选: video, image, 不传则返回所有类型"),
    sort_by: str = Query("create_time", description="排序字段: aweme_id, create_time, digg_count, collect_count, share_count, play_count"),
    sort_desc: bool = Query(True, description="是否降序排序"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取创作者的所有作品列表（包括视频和图集）
    
    Args:
        creator_id: 创作者的ID
        skip: 跳过的记录数
        limit: 返回的记录数
        content_type: 内容类型筛选: video, image, 不传则返回所有类型
        sort_by: 排序字段
        sort_desc: 是否降序排序
    """
    try:
        # 检查创作者是否存在
        creator = db.query(DouyinCreator).filter(
            DouyinCreator.id == creator_id
        ).first()
        
        if not creator:
            return ApiResponse(
                code=ErrorCode.NOT_FOUND,
                message="创作者不存在"
            )
            
        # 构建查询
        query = db.query(DouyinContent).filter(
            DouyinContent.creator_id == creator_id
        )
        
        # 根据内容类型筛选
        if content_type:
            query = query.filter(DouyinContent.content_type == content_type)
        
        # 默认按照is_top降序排序（置顶内容在前）
        query = query.order_by(desc(DouyinContent.is_top))
        
        # 添加排序
        sort_field = getattr(DouyinContent, sort_by, DouyinContent.create_time)
        if sort_desc:
            query = query.order_by(desc(DouyinContent.is_top), desc(sort_field))
        else:
            query = query.order_by(desc(DouyinContent.is_top), sort_field)
        
        # 获取总记录数
        total = query.count()
        
        # 获取分页数据
        contents = query.offset(skip).limit(limit).all()
        
        # 处理返回数据，添加封面和图片文件ID
        result_contents = []
        for content in contents:
            # 创建基本内容对象
            content_dict = {
                column.name: getattr(content, column.name)
                for column in content.__table__.columns
            }
            
            # 添加封面和图片文件ID
            if content.content_type == "video":
                # 按照优先级查询视频封面文件: dynamic_cover > origin_cover > cover
                cover_file = None
                
                # 1. 首先查询dynamic_cover
                dynamic_cover = db.query(DouyinContentFile).filter(
                    DouyinContentFile.aweme_id == content.aweme_id,
                    DouyinContentFile.file_type == "dynamic_cover"
                ).first()
                
                if dynamic_cover and dynamic_cover.file_path and os.path.exists(dynamic_cover.file_path):
                    cover_file = dynamic_cover
                else:
                    # 2. 其次查询origin_cover
                    origin_cover = db.query(DouyinContentFile).filter(
                        DouyinContentFile.aweme_id == content.aweme_id,
                        DouyinContentFile.file_type == "origin_cover"
                    ).first()
                    
                    if origin_cover and origin_cover.file_path and os.path.exists(origin_cover.file_path):
                        cover_file = origin_cover
                    else:
                        # 3. 最后查询普通cover
                        normal_cover = db.query(DouyinContentFile).filter(
                            DouyinContentFile.aweme_id == content.aweme_id,
                            DouyinContentFile.file_type == "cover"
                        ).first()
                        
                        if normal_cover and normal_cover.file_path and os.path.exists(normal_cover.file_path):
                            cover_file = normal_cover
                
                if cover_file:
                    # 返回文件ID
                    content_dict["cover_file_id"] = cover_file.id
                else:
                    content_dict["cover_file_id"] = None
                
                content_dict["image_file_ids"] = None
                
            elif content.content_type == "image":
                # 查询图集中的图片文件
                image_files = db.query(DouyinContentFile).filter(
                    DouyinContentFile.aweme_id == content.aweme_id,
                    DouyinContentFile.file_type == "image"
                ).order_by(DouyinContentFile.file_index).all()
                
                if image_files:
                    # 返回文件ID列表
                    content_dict["image_file_ids"] = [image_file.id for image_file in image_files]
                else:
                    content_dict["image_file_ids"] = []
                
                content_dict["cover_file_id"] = None
            
            result_contents.append(content_dict)
        
        return ApiResponse(
            code=200,
            message="获取作品列表成功",
            data=PaginationResponse(
                items=result_contents,
                total=total
            )
        )
    except Exception as e:
        return ApiResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取作品列表失败: {str(e)}"
        )

@router.get("/files/{file_id}", response_class=StreamingResponse)
async def get_file_by_id(
    file_id: int,
    db: Session = Depends(get_db),
):
    """通过文件ID获取文件内容"""
    try:
        # 查询文件记录
        file_record = db.query(DouyinContentFile).filter(
            DouyinContentFile.id == file_id
        ).first()
        
        if not file_record or not file_record.file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path = file_record.file_path
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 根据文件类型设置不同的媒体类型
        media_type = "image/jpeg"  # 默认为图片
        if file_record.file_type == "video":
            media_type = "video/mp4"
        elif file_record.file_type in ["cover", "origin_cover", "dynamic_cover"]:
            media_type = "image/jpeg"
    
        def iterfile():
            with open(file_path, "rb") as f:
                yield from f
        
        return StreamingResponse(iterfile(), media_type=media_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")
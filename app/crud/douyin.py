from typing import List, Optional, Union, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.douyin import DouyinContentFile, DouyinContent
from app.schemas.douyin import (
    DouyinContentFileCreate, DouyinContentFileUpdate, 
    DouyinContentCreate, DouyinContentUpdate
)

import logging
logging.basicConfig(level=logging.INFO)

# 内容文件相关操作
def create_content_file(db: Session, content_file: DouyinContentFileCreate) -> DouyinContentFile | None:
    """创建内容文件记录"""
    # 检查是否已存在相同的记录
    existing_file = db.query(DouyinContentFile).filter(
        DouyinContentFile.aweme_id == content_file.aweme_id,
        DouyinContentFile.file_type == content_file.file_type,
        DouyinContentFile.file_index == content_file.file_index
    ).first()
    
    if existing_file:
        return None
    
    # 如果不存在则创建新记录
    db_content_file = DouyinContentFile(
        content_id=content_file.content_id,
        aweme_id=content_file.aweme_id,
        file_type=content_file.file_type,
        file_index=content_file.file_index,
        file_path=content_file.file_path,
        cover_path=content_file.cover_path,
        origin_cover_path=content_file.origin_cover_path,
        dynamic_cover_path=content_file.dynamic_cover_path,
        file_size=content_file.file_size,
        file_hash=content_file.file_hash,
        download_status=content_file.download_status,
        error_message=content_file.error_message
    )
    db.add(db_content_file)
    db.commit()
    db.refresh(db_content_file)
    return db_content_file

def get_content_file(db: Session, content_file_id: int) -> Optional[DouyinContentFile]:
    """根据ID获取内容文件记录"""
    return db.query(DouyinContentFile).filter(DouyinContentFile.id == content_file_id).first()

def get_content_file_by_aweme_id_and_type(
    db: Session, 
    aweme_id: str, 
    file_type: str,
    file_index: Optional[int] = None
) -> Optional[DouyinContentFile]:
    """根据作品ID和文件类型获取内容文件记录"""
    query = db.query(DouyinContentFile).filter(
        DouyinContentFile.aweme_id == aweme_id,
        DouyinContentFile.file_type == file_type
    )
    
    if file_index is not None:
        query = query.filter(DouyinContentFile.file_index == file_index)
    
    return query.first()

def get_content_files(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    download_status: Optional[str] = None,
    file_type: Optional[str] = None
) -> List[DouyinContentFile]:
    """获取内容文件列表"""
    query = db.query(DouyinContentFile)
    
    if download_status:
        query = query.filter(DouyinContentFile.download_status == download_status)
    
    if file_type:
        query = query.filter(DouyinContentFile.file_type == file_type)
    
    return query.offset(skip).limit(limit).all()

def update_content_file(
    db: Session,
    content_file_id: int,
    content_file_update: DouyinContentFileUpdate
) -> Optional[DouyinContentFile]:
    """更新内容文件记录"""
    db_content_file = db.query(DouyinContentFile).filter(DouyinContentFile.id == content_file_id).first()
    if not db_content_file:
        return None
    
    update_data = content_file_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_content_file, key, value)
    
    db.commit()
    db.refresh(db_content_file)
    return db_content_file

def delete_content_file(db: Session, content_file_id: int) -> bool:
    """删除内容文件记录"""
    db_content_file = db.query(DouyinContentFile).filter(DouyinContentFile.id == content_file_id).first()
    if not db_content_file:
        return False
    
    db.delete(db_content_file)
    db.commit()
    return True

def get_pending_content_files(db: Session, limit: int = 10, file_type: Optional[str] = None) -> List[DouyinContentFile]:
    """获取待下载的内容文件列表"""
    query = db.query(DouyinContentFile).filter(DouyinContentFile.download_status == "pending")
    
    if file_type:
        query = query.filter(DouyinContentFile.file_type == file_type)
    
    return query.limit(limit).all()

def update_content_file_download_status(
    db: Session,
    content_file_id: int,
    status: str,
    error_message: Optional[str] = None
) -> Optional[DouyinContentFile]:
    """更新内容文件下载状态"""
    db_content_file = db.query(DouyinContentFile).filter(DouyinContentFile.id == content_file_id).first()
    if not db_content_file:
        return None
    
    db_content_file.download_status = status
    if error_message:
        db_content_file.error_message = error_message
    
    db.commit()
    db.refresh(db_content_file)
    return db_content_file

def create_content_files_bulk(db: Session, content_files: List[DouyinContentFileCreate]) -> Dict[str, List[DouyinContentFile]]:
    """批量创建内容文件记录"""
    created_files = []
    skipped_files = []
    
    for content_file in content_files:
        # 检查是否已存在相同的记录
        existing_file = db.query(DouyinContentFile).filter(
            DouyinContentFile.aweme_id == content_file.aweme_id,
            DouyinContentFile.file_type == content_file.file_type,
            DouyinContentFile.file_index == content_file.file_index
        ).first()
        
        if existing_file:
            skipped_files.append(existing_file)
            continue
        
        # 如果不存在则创建新记录
        db_content_file = DouyinContentFile(
            content_id=content_file.content_id,
            aweme_id=content_file.aweme_id,
            file_type=content_file.file_type,
            file_index=content_file.file_index,
            file_path=content_file.file_path,
            cover_path=content_file.cover_path,
            origin_cover_path=content_file.origin_cover_path,
            dynamic_cover_path=content_file.dynamic_cover_path,
            file_size=content_file.file_size,
            file_hash=content_file.file_hash,
            download_status=content_file.download_status,
            error_message=content_file.error_message
        )
        db.add(db_content_file)
        created_files.append(db_content_file)
    
    if created_files:
        db.commit()
        for file in created_files:
            db.refresh(file)
    
    return {
        "created": created_files,
        "skipped": skipped_files
    }

# 内容相关操作
def create_content(db: Session, content: DouyinContentCreate) -> Optional[DouyinContent]:
    """创建内容记录"""
    # 检查是否已存在相同的 aweme_id
    existing_content = db.query(DouyinContent).filter(
        DouyinContent.aweme_id == content.aweme_id
    ).first()
    
    if existing_content:
        return None
    
    # 如果不存在则创建新记录
    db_content = DouyinContent(**content.model_dump())
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content

def create_contents_bulk(db: Session, contents: List[DouyinContentCreate]) -> Dict[str, List[DouyinContent]]:
    """批量创建内容记录"""
    created_contents = []
    skipped_contents = []
    
    for content in contents:
        # 检查是否已存在相同的 aweme_id
        existing_content = db.query(DouyinContent).filter(
            DouyinContent.aweme_id == content.aweme_id
        ).first()
        
        if existing_content:
            skipped_contents.append(existing_content)
            continue
        
        # 如果不存在则创建新记录
        db_content = DouyinContent(**content.model_dump())
        db.add(db_content)
        created_contents.append(db_content)
    
    if created_contents:
        db.commit()
        for content in created_contents:
            db.refresh(content)
    
    return {
        "created": created_contents,
        "skipped": skipped_contents
    }

def get_content(db: Session, content_id: int) -> Optional[DouyinContent]:
    """根据ID获取内容记录"""
    return db.query(DouyinContent).filter(DouyinContent.id == content_id).first()

def get_content_by_aweme_id(db: Session, aweme_id: str) -> Optional[DouyinContent]:
    """根据作品ID获取内容记录"""
    return db.query(DouyinContent).filter(DouyinContent.aweme_id == aweme_id).first()

def get_contents(
    db: Session,
    creator_id: Optional[int] = None,
    content_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[DouyinContent]:
    """获取内容列表"""
    query = db.query(DouyinContent)
    
    if creator_id:
        query = query.filter(DouyinContent.creator_id == creator_id)
    
    if content_type:
        query = query.filter(DouyinContent.content_type == content_type)
    
    return query.offset(skip).limit(limit).all()

def get_contents_count(
    db: Session,
    creator_id: Optional[int] = None,
    content_type: Optional[str] = None
) -> int:
    """获取内容数量"""
    query = db.query(DouyinContent)
    
    if creator_id:
        query = query.filter(DouyinContent.creator_id == creator_id)
    
    if content_type:
        query = query.filter(DouyinContent.content_type == content_type)
    
    return query.count()

def update_content(
    db: Session,
    content_id: int,
    content_update: DouyinContentUpdate
) -> Optional[DouyinContent]:
    """更新内容记录"""
    db_content = db.query(DouyinContent).filter(DouyinContent.id == content_id).first()
    if not db_content:
        return None
    
    update_data = content_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_content, key, value)
    
    db.commit()
    db.refresh(db_content)
    return db_content

def delete_content(db: Session, content_id: int) -> bool:
    """删除内容记录"""
    db_content = db.query(DouyinContent).filter(DouyinContent.id == content_id).first()
    if not db_content:
        return False
    
    db.delete(db_content)
    db.commit()
    return True

# 为了向后兼容，提供一些辅助函数
def get_video_by_aweme_id(db: Session, aweme_id: str) -> Optional[DouyinContent]:
    """根据视频ID获取视频记录"""
    return db.query(DouyinContent).filter(
        DouyinContent.aweme_id == aweme_id,
        DouyinContent.content_type == "video"
    ).first()

def get_videos(
    db: Session,
    creator_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[DouyinContent]:
    """获取视频列表"""
    return get_contents(db, creator_id, "video", skip, limit)

def get_videos_count(
    db: Session,
    creator_id: Optional[int] = None
) -> int:
    """获取视频数量"""
    return get_contents_count(db, creator_id, "video")

def get_image_post_by_aweme_id(db: Session, aweme_id: str) -> Optional[DouyinContent]:
    """根据图集ID获取图集记录"""
    return db.query(DouyinContent).filter(
        DouyinContent.aweme_id == aweme_id,
        DouyinContent.content_type == "image"
    ).first()

def get_image_posts(
    db: Session,
    creator_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[DouyinContent]:
    """获取图集列表"""
    return get_contents(db, creator_id, "image", skip, limit)

def get_image_posts_count(
    db: Session,
    creator_id: Optional[int] = None
) -> int:
    """获取图集数量"""
    return get_contents_count(db, creator_id, "image")

def get_video_file_by_aweme_id(db: Session, aweme_id: str) -> Optional[DouyinContentFile]:
    """根据视频ID获取视频文件记录"""
    return get_content_file_by_aweme_id_and_type(db, aweme_id, "video")

def get_image_files_by_aweme_id(
    db: Session, 
    aweme_id: str
) -> List[DouyinContentFile]:
    """根据图集ID获取图片文件记录列表"""
    return db.query(DouyinContentFile).filter(
        DouyinContentFile.aweme_id == aweme_id,
        DouyinContentFile.file_type == "image"
    ).all()

def get_image_file_by_index(
    db: Session, 
    aweme_id: str, 
    image_index: int
) -> Optional[DouyinContentFile]:
    """根据图集ID和图片索引获取图片文件记录"""
    return get_content_file_by_aweme_id_and_type(db, aweme_id, "image", image_index)

if __name__ == "__main__":
    
    # from app.db.session import get_db_context, base_db
    # from app.models.douyin import DouyinCreator
    
    # base_db.init_db()

    pass
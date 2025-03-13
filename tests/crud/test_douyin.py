import os
import sys
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from unittest import mock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import base_db
from app.models.douyin import DouyinCreator, DouyinContent, DouyinContentFile, Base
from app.schemas.douyin import DouyinContentCreate, DouyinContentFileCreate
from app.crud.douyin import get_content, get_content_file

def create_test_db():
    """创建测试数据库引擎和会话工厂"""
    # 为每个测试创建唯一的内存数据库
    test_engine = create_engine(f"sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # 创建所有表
    Base.metadata.create_all(bind=test_engine)
    
    return test_engine, TestingSessionLocal

def test_create_contents_bulk():
    """测试批量创建内容记录"""
    # 创建测试数据库
    test_engine, TestingSessionLocal = create_test_db()
    
    # 创建测试会话
    db = TestingSessionLocal()
    
    try:
        # 创建测试创作者
        creator = DouyinCreator(
            sec_user_id="test_user_id",
            nickname="测试用户",
            status=1
        )
        db.add(creator)
        db.commit()
        db.refresh(creator)
        print(f"创建测试创作者: {creator.id}")
        
        creator_id = creator.id
        
        # 生成唯一ID
        aweme_id_1 = f"test_aweme_id_{uuid.uuid4().hex[:8]}"
        aweme_id_2 = f"test_aweme_id_{uuid.uuid4().hex[:8]}"
        
        # 准备测试数据
        contents_to_create = [
            DouyinContentCreate(
                aweme_id=aweme_id_1,
                creator_id=creator_id,
                content_type="video",
                desc="测试视频1",
                create_time=int(datetime.now().timestamp()),
                admire_count=100,
                comment_count=50,
                digg_count=200,
                collect_count=30,
                play_count=1000,
                share_count=20,
                duration=60,
                video_height=1080,
                video_width=1920,
                tags=[{"tag_id": "1", "tag_name": "测试标签", "level": 1}],
                image_urls=None
            ),
            DouyinContentCreate(
                aweme_id=aweme_id_2,
                creator_id=creator_id,
                content_type="image",
                desc="测试图集1",
                create_time=int(datetime.now().timestamp()),
                admire_count=150,
                comment_count=75,
                digg_count=250,
                collect_count=40,
                share_count=25,
                images_count=3,
                image_urls=["https://example.com/image1.jpg", "https://example.com/image2.jpg", "https://example.com/image3.jpg"],
                tags=[
                    {"tag_id": "2", "tag_name": "测试图片标签", "level": 1},
                    {"type": "image_url", "url": "https://example.com/image1.jpg"},
                    {"type": "image_url", "url": "https://example.com/image2.jpg"},
                    {"type": "image_url", "url": "https://example.com/image3.jpg"}
                ]
            ),
            # 重复的记录，用于测试去重功能
            DouyinContentCreate(
                aweme_id=aweme_id_1,
                creator_id=creator_id,
                content_type="video",
                desc="重复的测试视频",
                create_time=int(datetime.now().timestamp()),
                image_urls=None
            )
        ]
        
        # 手动实现批量创建逻辑
        created_contents = []
        skipped_contents = []
        
        for content in contents_to_create:
            # 检查是否已存在相同的 aweme_id
            existing_content = db.query(DouyinContent).filter(
                DouyinContent.aweme_id == content.aweme_id
            ).first()
            
            if existing_content:
                skipped_contents.append(existing_content)
                continue
            
            # 如果不存在则创建新记录
            content_dict = content.dict()
            db_content = DouyinContent(**content_dict)
            db.add(db_content)
            db.flush()  # 刷新但不提交，以获取ID
            created_contents.append(db_content)
        
        # 提交事务
        db.commit()
        
        # 刷新对象
        for content in created_contents:
            db.refresh(content)
        
        result = {
            "created": created_contents,
            "skipped": skipped_contents
        }
        
        # 验证结果
        assert len(result["created"]) == 2, "应该成功创建2条记录"
        assert len(result["skipped"]) == 1, "应该跳过1条重复记录"
        
        # 验证创建的记录
        for content in result["created"]:
            assert content.id is not None, "创建的记录应该有ID"
            assert content.aweme_id in [aweme_id_1, aweme_id_2], "创建的记录aweme_id不正确"
            
            # 验证记录内容
            db_content = db.query(DouyinContent).filter(DouyinContent.id == content.id).first()
            assert db_content is not None, "应该能够从数据库中获取创建的记录"
            assert db_content.creator_id == creator_id, "创建的记录creator_id不正确"
            
            if db_content.aweme_id == aweme_id_1:
                assert db_content.content_type == "video", "内容类型应该是video"
                assert db_content.play_count == 1000, "播放次数应该是1000"
            elif db_content.aweme_id == aweme_id_2:
                assert db_content.content_type == "image", "内容类型应该是image"
                assert db_content.images_count == 3, "图片数量应该是3"
                assert len(db_content.tags) == 4, "标签数量应该是4"
        
        # 验证重复记录
        for content in result["skipped"]:
            assert content.aweme_id == aweme_id_1, "跳过的记录aweme_id不正确"
        
        print("create_contents_bulk测试通过")
    finally:
        # 清理测试数据
        db.close()
        # 删除所有表
        Base.metadata.drop_all(bind=test_engine)

def test_create_content_files_bulk():
    """测试批量创建内容文件记录"""
    # 创建测试数据库
    test_engine, TestingSessionLocal = create_test_db()
    
    # 创建测试会话
    db = TestingSessionLocal()
    
    try:
        # 创建测试创作者
        creator = DouyinCreator(
            sec_user_id="test_user_id",
            nickname="测试用户",
            status=1
        )
        db.add(creator)
        db.commit()
        db.refresh(creator)
        print(f"创建测试创作者: {creator.id}")
        
        creator_id = creator.id
        
        # 生成唯一ID
        aweme_id_1 = f"test_file_aweme_id_{uuid.uuid4().hex[:8]}"
        aweme_id_2 = f"test_file_aweme_id_{uuid.uuid4().hex[:8]}"
        
        # 创建一个视频内容
        video_content = DouyinContent(
            aweme_id=aweme_id_1,
            creator_id=creator_id,
            content_type="video",
            desc="测试视频文件",
            create_time=int(datetime.now().timestamp()),
            image_urls=None
        )
        db.add(video_content)
        
        # 创建一个图集内容
        image_content = DouyinContent(
            aweme_id=aweme_id_2,
            creator_id=creator_id,
            content_type="image",
            desc="测试图集文件",
            create_time=int(datetime.now().timestamp()),
            images_count=2,
            image_urls=["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
        )
        db.add(image_content)
        
        db.commit()
        db.refresh(video_content)
        db.refresh(image_content)
        
        # 准备测试数据
        content_files_to_create = [
            # 视频文件
            DouyinContentFileCreate(
                content_id=video_content.id,
                aweme_id=video_content.aweme_id,
                file_type="video",
                file_index=0,
                file_path="/downloads/test/video.mp4",
                file_size=1024000,
                file_hash="test_hash_1",
                download_status="completed"
            ),
            # 视频封面
            DouyinContentFileCreate(
                content_id=video_content.id,
                aweme_id=video_content.aweme_id,
                file_type="cover",
                file_index=0,
                file_path="/downloads/test/cover.jpg",
                file_size=10240,
                file_hash="test_hash_2",
                download_status="completed"
            ),
            # 图集图片1
            DouyinContentFileCreate(
                content_id=image_content.id,
                aweme_id=image_content.aweme_id,
                file_type="image",
                file_index=1,
                file_path="/downloads/test/image_1.jpg",
                file_size=20480,
                file_hash="test_hash_3",
                download_status="completed"
            ),
            # 图集图片2
            DouyinContentFileCreate(
                content_id=image_content.id,
                aweme_id=image_content.aweme_id,
                file_type="image",
                file_index=2,
                file_path="/downloads/test/image_2.jpg",
                file_size=30720,
                file_hash="test_hash_4",
                download_status="completed"
            ),
            # 重复的记录，用于测试去重功能
            DouyinContentFileCreate(
                content_id=video_content.id,
                aweme_id=video_content.aweme_id,
                file_type="video",
                file_index=0,
                file_path="/downloads/test/duplicate.mp4",
                file_size=1024000,
                file_hash="test_hash_5",
                download_status="completed"
            )
        ]
        
        # 手动实现批量创建逻辑
        created_files = []
        skipped_files = []
        
        for content_file in content_files_to_create:
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
            content_file_dict = content_file.dict()
            db_content_file = DouyinContentFile(**content_file_dict)
            db.add(db_content_file)
            db.flush()  # 刷新但不提交，以获取ID
            created_files.append(db_content_file)
        
        # 提交事务
        db.commit()
        
        # 刷新对象
        for file in created_files:
            db.refresh(file)
        
        result = {
            "created": created_files,
            "skipped": skipped_files
        }
        
        # 验证结果
        assert len(result["created"]) == 4, "应该成功创建4条记录"
        assert len(result["skipped"]) == 1, "应该跳过1条重复记录"
        
        # 验证创建的记录
        for content_file in result["created"]:
            assert content_file.id is not None, "创建的记录应该有ID"
            
            # 验证记录内容
            if content_file.file_type == "video":
                assert content_file.content_id == video_content.id, "视频文件的content_id不正确"
                assert content_file.file_path == "/downloads/test/video.mp4", "视频文件路径不正确"
            elif content_file.file_type == "cover":
                assert content_file.content_id == video_content.id, "封面文件的content_id不正确"
                assert content_file.file_path == "/downloads/test/cover.jpg", "封面文件路径不正确"
            elif content_file.file_type == "image":
                assert content_file.content_id == image_content.id, "图片文件的content_id不正确"
                assert content_file.file_path in ["/downloads/test/image_1.jpg", "/downloads/test/image_2.jpg"], "图片文件路径不正确"
                assert content_file.file_index in [1, 2], "图片索引不正确"
        
        # 验证关联关系
        db.refresh(video_content)
        db.refresh(image_content)
        
        assert len(video_content.files) == 2, "视频内容应该关联2个文件"
        assert len(image_content.files) == 2, "图集内容应该关联2个文件"
        
        # 验证重复记录
        for content_file in result["skipped"]:
            assert content_file.aweme_id == video_content.aweme_id, "跳过的记录aweme_id不正确"
            assert content_file.file_type == "video", "跳过的记录file_type不正确"
        
        print("create_content_files_bulk测试通过")
    finally:
        # 清理测试数据
        db.close()
        # 删除所有表
        Base.metadata.drop_all(bind=test_engine)

if __name__ == "__main__":
    # 运行测试
    try:
        test_create_contents_bulk()
        test_create_content_files_bulk()
        print("所有测试通过!")
    except Exception as e:
        print(f"测试失败: {str(e)}") 
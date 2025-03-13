"""
数据表迁移脚本
将DouyinVideo、DouyinVideoFile、DouyinImagePost、DouyinImageFile合并为DouyinContent和DouyinContentFile
"""
import sys
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# 添加项目根目录到系统路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db.session import get_db
from app.core.config import settings
from app.models.douyin import DouyinContent, DouyinContentFile

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_data():
    """迁移数据从旧表到新表"""
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 1. 检查旧表是否存在
        tables_to_check = ["douyin_videos", "douyin_video_files", "douyin_image_posts", "douyin_image_files"]
        for table in tables_to_check:
            result = db.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
            exists = result.scalar()
            if not exists:
                logger.warning(f"表 {table} 不存在，跳过迁移")
                return
        
        # 2. 迁移视频数据到内容表
        logger.info("开始迁移视频数据到内容表...")
        db.execute(text("""
            INSERT INTO douyin_contents (
                aweme_id, creator_id, content_type, desc, group_id, create_time, is_top, 
                aweme_type, media_type, admire_count, comment_count, digg_count, 
                collect_count, play_count, share_count, duration, video_height, 
                video_width, tags, created_at, updated_at
            )
            SELECT 
                aweme_id, creator_id, 'video', desc, group_id, create_time, is_top, 
                aweme_type, media_type, admire_count, comment_count, digg_count, 
                collect_count, play_count, share_count, duration, video_height, 
                video_width, video_tags, created_at, updated_at
            FROM douyin_videos
            ON CONFLICT (aweme_id) DO NOTHING
        """))
        
        # 3. 迁移图集数据到内容表
        logger.info("开始迁移图集数据到内容表...")
        db.execute(text("""
            INSERT INTO douyin_contents (
                aweme_id, creator_id, content_type, desc, group_id, create_time, is_top, 
                aweme_type, media_type, admire_count, comment_count, digg_count, 
                collect_count, share_count, images_count, image_urls, tags, 
                created_at, updated_at
            )
            SELECT 
                aweme_id, creator_id, 'image_post', desc, group_id, create_time, is_top, 
                68, 2, admire_count, comment_count, digg_count, 
                collect_count, 0, share_count, images_count, image_urls, image_tags, 
                created_at, updated_at
            FROM douyin_image_posts
            ON CONFLICT (aweme_id) DO NOTHING
        """))
        
        # 4. 获取内容ID映射
        logger.info("获取内容ID映射...")
        video_id_mapping = {}
        image_post_id_mapping = {}
        
        # 获取视频ID映射
        video_mappings = db.execute(text("""
            SELECT v.id as old_id, c.id as new_id, c.aweme_id
            FROM douyin_videos v
            JOIN douyin_contents c ON v.aweme_id = c.aweme_id
            WHERE c.content_type = 'video'
        """)).fetchall()
        
        for row in video_mappings:
            video_id_mapping[row.old_id] = row.new_id
        
        # 获取图集ID映射
        image_post_mappings = db.execute(text("""
            SELECT p.id as old_id, c.id as new_id, c.aweme_id
            FROM douyin_image_posts p
            JOIN douyin_contents c ON p.aweme_id = c.aweme_id
            WHERE c.content_type = 'image_post'
        """)).fetchall()
        
        for row in image_post_mappings:
            image_post_id_mapping[row.old_id] = row.new_id
        
        # 5. 迁移视频文件数据到内容文件表
        logger.info("开始迁移视频文件数据到内容文件表...")
        for old_id, new_id in video_id_mapping.items():
            # 迁移视频文件
            db.execute(text("""
                INSERT INTO douyin_content_files (
                    content_id, aweme_id, file_type, file_path, cover_path, 
                    origin_cover_path, dynamic_cover_path, file_size, file_hash, 
                    download_status, error_message, created_at, updated_at
                )
                SELECT 
                    :new_id, aweme_id, 'video', video_path, cover_path, 
                    origin_cover_path, dynamic_cover_path, video_size, video_hash, 
                    download_status, error_message, created_at, updated_at
                FROM douyin_video_files
                WHERE aweme_id = (SELECT aweme_id FROM douyin_videos WHERE id = :old_id)
                ON CONFLICT (aweme_id, file_type, COALESCE(file_index, -1)) DO NOTHING
            """), {"new_id": new_id, "old_id": old_id})
        
        # 6. 迁移图片文件数据到内容文件表
        logger.info("开始迁移图片文件数据到内容文件表...")
        for old_id, new_id in image_post_id_mapping.items():
            # 迁移图片文件
            db.execute(text("""
                INSERT INTO douyin_content_files (
                    content_id, aweme_id, file_type, file_index, file_path, 
                    file_size, file_hash, download_status, error_message, 
                    created_at, updated_at
                )
                SELECT 
                    :new_id, aweme_id, 'image', image_index, image_path, 
                    image_size, image_hash, download_status, error_message, 
                    created_at, updated_at
                FROM douyin_image_files
                WHERE image_post_id = :old_id
                ON CONFLICT (aweme_id, file_type, COALESCE(file_index, -1)) DO NOTHING
            """), {"new_id": new_id, "old_id": old_id})
        
        # 7. 提交事务
        db.commit()
        logger.info("数据迁移完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"数据迁移失败: {str(e)}")
        raise
    finally:
        db.close()

def verify_migration():
    """验证数据迁移是否成功"""
    db = next(get_db())
    
    try:
        # 1. 检查内容表数据数量
        video_count = db.execute(text("SELECT COUNT(*) FROM douyin_videos")).scalar()
        image_post_count = db.execute(text("SELECT COUNT(*) FROM douyin_image_posts")).scalar()
        content_count = db.execute(text("SELECT COUNT(*) FROM douyin_contents")).scalar()
        
        logger.info(f"原视频表记录数: {video_count}")
        logger.info(f"原图集表记录数: {image_post_count}")
        logger.info(f"新内容表记录数: {content_count}")
        
        # 2. 检查内容文件表数据数量
        video_file_count = db.execute(text("SELECT COUNT(*) FROM douyin_video_files")).scalar()
        image_file_count = db.execute(text("SELECT COUNT(*) FROM douyin_image_files")).scalar()
        content_file_count = db.execute(text("SELECT COUNT(*) FROM douyin_content_files")).scalar()
        
        logger.info(f"原视频文件表记录数: {video_file_count}")
        logger.info(f"原图片文件表记录数: {image_file_count}")
        logger.info(f"新内容文件表记录数: {content_file_count}")
        
        # 3. 检查是否有丢失的数据
        if content_count < (video_count + image_post_count):
            logger.warning("警告: 内容表记录数少于原视频表和图集表记录数之和，可能有数据丢失")
        
        if content_file_count < (video_file_count + image_file_count):
            logger.warning("警告: 内容文件表记录数少于原视频文件表和图片文件表记录数之和，可能有数据丢失")
        
    except Exception as e:
        logger.error(f"验证数据迁移失败: {str(e)}")
        raise
    finally:
        db.close()

def drop_old_tables():
    """删除旧表"""
    db = next(get_db())
    
    try:
        # 询问用户确认
        confirm = input("确认要删除旧表吗? (y/n): ")
        if confirm.lower() != 'y':
            logger.info("取消删除旧表")
            return
        
        # 删除旧表
        tables_to_drop = ["douyin_video_files", "douyin_videos", "douyin_image_files", "douyin_image_posts"]
        for table in tables_to_drop:
            db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        
        db.commit()
        logger.info("旧表删除成功")
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除旧表失败: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据表迁移工具")
    parser.add_argument("--migrate", action="store_true", help="执行数据迁移")
    parser.add_argument("--verify", action="store_true", help="验证数据迁移")
    parser.add_argument("--drop-old", action="store_true", help="删除旧表")
    
    args = parser.parse_args()
    
    if args.migrate:
        migrate_data()
    
    if args.verify:
        verify_migration()
    
    if args.drop_old:
        drop_old_tables()
    
    if not (args.migrate or args.verify or args.drop_old):
        parser.print_help() 
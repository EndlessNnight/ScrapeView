import asyncio
from app.scripts.douyin.tiktok_api import TikTokApi
from app.db.session import get_db_context, base_db
from app.models.douyin import DouyinCreator, DouyinContent
from app.services.douyin import get_douyin_cookie
from app.scripts.douyin.downloader import DownloadManager
from app.scripts.douyin.schemas import DownloadTask, CoverUrls
from app.core.task_context import get_task_context
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_task():
    """
        测试任务
    """
    print("测试任务")

async def test_task_async():
    print("测试异步任务: ", time.time())
    await asyncio.sleep(10)
    print("测试异步任务结束: ", time.time())


def collect_creator_videos(sec_user_id: str = None):
    """采集抖音创作者的视频数据
    
    Args:
        sec_user_id: 创作者的sec_user_id。如果为None，则从任务参数中获取
    """
    try:
        context = get_task_context()
        print(f"任务上下文: {context}")
        if not context:
            raise ValueError("未找到任务上下文")
            
        if not sec_user_id:
            if not context.get('sec_user_id'):
                raise ValueError("未提供sec_user_id参数")
            sec_user_id = context['sec_user_id']
            
        user_id = context.get('user_id')
        if not user_id:
            raise ValueError("未提供user_id参数")
            
        logger.info(f"开始采集创作者 {sec_user_id} 的视频数据")
        
        with get_db_context() as db:
            saved_cookie = get_douyin_cookie(db, user_id)
            if not saved_cookie:
                raise ValueError("未找到保存的Cookie")
                
            # 获取创作者信息
            creator = db.query(DouyinCreator).filter_by(sec_user_id=sec_user_id).first()
            if not creator:
                logger.error(f"创作者 {sec_user_id} 不存在")
                return
            
            # 获取创作者的last_aweme_id
            last_aweme_id = creator.last_aweme_id or "0"
            logger.info(f"创作者 {sec_user_id} 的last_aweme_id: {last_aweme_id}")
            
            # 初始化下载管理器
            downloader = DownloadManager()
            
            # 初始化API客户端
            api = TikTokApi(cookie=saved_cookie)
            
            # 分页获取视频列表
            max_cursor = 0
            count = 40
            has_more = True
            should_stop = False  # 标记是否应该停止采集
            
            # 用于收集所有非置顶视频和图集的aweme_id
            all_non_top_aweme_ids = []
            
            while has_more and not should_stop:
                try:
                    # 获取视频列表
                    response = api.get_creator_video_list(
                        sec_user_id=sec_user_id,
                        count=count,
                        max_cursor=max_cursor
                    )
                    
                    if not response or not response.aweme_list:
                        logger.info(f"未获取到更多视频数据，结束采集")
                        break
                    
                    # 处理视频数据
                    # 批量处理视频数据
                    contents_to_update = []
                    contents_to_create = []
                    download_tasks = []
                    
                    # 检查是否有视频的aweme_id小于last_aweme_id
                    for aweme in response.aweme_list:
                        try:
                            # 如果视频的aweme_id小于last_aweme_id且不是置顶视频，则结束采集
                            if aweme.aweme_id < last_aweme_id and aweme.is_top != 1:
                                logger.info(f"发现视频 {aweme.aweme_id} 小于last_aweme_id {last_aweme_id} 且不是置顶视频，结束采集")
                                should_stop = True
                                break
                            
                            # 如果不是置顶视频/图集，则收集aweme_id用于更新last_aweme_id
                            if aweme.is_top != 1:
                                all_non_top_aweme_ids.append(aweme.aweme_id)
                            
                            # 确定内容类型
                            content_type = "image" if aweme.aweme_type == 68 else "video"
                            
                            # 检查内容是否已存在
                            existing_content = db.query(DouyinContent).filter_by(aweme_id=aweme.aweme_id).first()
                            
                            if existing_content:
                                # 更新内容统计数据
                                existing_content.admire_count = aweme.statistics.admire_count
                                existing_content.comment_count = aweme.statistics.comment_count
                                existing_content.digg_count = aweme.statistics.digg_count
                                existing_content.collect_count = aweme.statistics.collect_count
                                existing_content.share_count = aweme.statistics.share_count
                                
                                # 如果是视频，还需要更新播放次数
                                if content_type == "video":
                                    existing_content.play_count = aweme.statistics.play_count
                                
                                contents_to_update.append(existing_content)
                                continue
                            
                            # 准备新内容记录
                            content = DouyinContent(
                                creator_id=creator.id,
                                aweme_id=aweme.aweme_id,
                                desc=aweme.desc,
                                group_id=aweme.group_id,
                                create_time=aweme.create_time,
                                is_top=aweme.is_top,
                                content_type=content_type,
                                
                                # 统计信息
                                admire_count=aweme.statistics.admire_count,
                                comment_count=aweme.statistics.comment_count,
                                digg_count=aweme.statistics.digg_count,
                                collect_count=aweme.statistics.collect_count,
                                share_count=aweme.statistics.share_count,
                            )
                            
                            # 根据内容类型设置特定字段
                            if content_type == "video":
                                content.aweme_type = aweme.aweme_type
                                content.media_type = aweme.media_type
                                content.play_count = aweme.statistics.play_count
                                content.duration = aweme.video.duration if aweme.video else None
                                content.video_height = aweme.video.play_addr.height if aweme.video and aweme.video.play_addr else None
                                content.video_width = aweme.video.play_addr.width if aweme.video and aweme.video.play_addr else None
                            elif content_type == "image":
                                content.images_count = len(aweme.images) if aweme.images else 0
                                content.image_urls = [img.url_list[0] for img in aweme.images] if aweme.images else []
                            content.tags = [{
                                "tag_id": tag.tag_id,
                                "tag_name": tag.tag_name,
                                "level": tag.level
                            } for tag in (aweme.video_tag or [])]
                            
                            # 保存内容记录并获取ID
                            db.add(content)
                            try:
                                db.flush()
                                db.refresh(content)
                                # logger.info(f"成功创建内容记录，ID: {content.id}, 类型: {content_type}")
                                
                                # 添加到批量创建列表
                                contents_to_create.append(content)
                                
                                # 创建下载任务
                                if content_type == "video":
                                    # 获取视频URL列表
                                    video_urls = []
                                    if aweme.video and aweme.video.play_addr and aweme.video.play_addr.url_list:
                                        video_urls.extend(aweme.video.play_addr.url_list)
                                    
                                    # 获取封面URL列表
                                    cover_urls = []
                                    if aweme.video:
                                        if aweme.video.dynamic_cover and aweme.video.dynamic_cover.url_list:
                                            cover_urls.append(CoverUrls(cover_type='dynamic_cover', url=aweme.video.dynamic_cover.url_list))
                                        if aweme.video.cover and aweme.video.cover.url_list:
                                            cover_urls.append(CoverUrls(cover_type='cover', url=aweme.video.cover.url_list))
                                        if aweme.video.origin_cover and aweme.video.origin_cover.url_list:
                                            cover_urls.append(CoverUrls(cover_type='origin_cover', url=aweme.video.origin_cover.url_list))
                                    
                                    download_tasks.append(DownloadTask(
                                        sec_user_id=sec_user_id,
                                        aweme_id=aweme.aweme_id,
                                        image_urls=[],
                                        video_urls=video_urls,
                                        cover_urls=cover_urls,
                                        content_id=content.id
                                    ))
                                elif content_type == "image" and aweme.images:
                                    download_tasks.append(DownloadTask(
                                        sec_user_id=sec_user_id,
                                        aweme_id=aweme.aweme_id,
                                        image_urls=[img.url_list[0] for img in aweme.images],
                                        video_urls=[],
                                        cover_urls=[],
                                        content_id=content.id
                                    ))
                                    # logger.info(f"已创建图集 {aweme.aweme_id} 的下载任务，content_id: {content.id}")
                            except Exception as e:
                                logger.error(f"保存内容记录失败: {str(e)}")
                                db.rollback()
                                continue
                            
                        except Exception as e:
                            logger.error(f"处理数据失败: {str(e)}")
                            continue
                    
                    try:
                        # 批量更新现有记录
                        if contents_to_update:
                            db.bulk_save_objects(contents_to_update)
                        
                        # 批量创建新记录
                        if contents_to_create:
                            db.add_all(contents_to_create)
                            
                        # 提交所有更改
                        db.commit()
                            
                        logger.info(f"成功批量保存 {len(contents_to_create)} 个新内容，更新 {len(contents_to_update)} 个现有内容")
                        
                        # 使用并发下载资源
                        if download_tasks:
                            try:
                                # 初始化下载管理器
                                downloader = DownloadManager(max_workers=3)
                                
                                download_results = downloader.batch_download_videos_with_db(db, download_tasks)
                                logger.info(f"批量下载结果: 成功={len(download_results['success'])}, 失败={len(download_results['failed'])}")
                                if download_results['failed']:
                                    logger.warning(f"以下内容下载失败: {download_results['failed']}")
                                
                                # 提交下载记录
                                db.commit()
                            except Exception as e:
                                logger.error(f"下载任务执行失败: {str(e)}")
                                db.rollback()
                        
                    except Exception as e:
                        logger.error(f"批量保存数据失败: {str(e)}")
                        db.rollback()
                    
                    # 更新分页信息
                    has_more = response.has_more == 1
                    max_cursor = response.max_cursor
                    logger.info(f"分页信息: has_more={has_more}, max_cursor={max_cursor}")
                    
                    # 如果应该停止采集，则跳出循环
                    if should_stop:
                        break
                    
                    # 添加延时，避免请求过快
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"获取列表失败: {str(e)}")
                    break
            
            # 更新创作者的last_aweme_id
            if all_non_top_aweme_ids:
                max_aweme_id = max(all_non_top_aweme_ids)
                if max_aweme_id > last_aweme_id:
                    creator.last_aweme_id = max_aweme_id
                    db.commit()
                    logger.info(f"已更新创作者 {sec_user_id} 的last_aweme_id为 {max_aweme_id}")
            
            logger.info(f"创作者 {sec_user_id} 的数据采集完成")
            
    except Exception as e:
        logger.error(f"采集创作者 {sec_user_id} 的视频数据失败: {str(e)}")
        raise


async def collect_creator_info():
    """采集抖音创作者信息"""
    logger.info(f"开始采集创作者信息")
    

    context = get_task_context()
    if not context:
        raise ValueError("未找到任务上下文")

    user_id = context.get('user_id')
    if not user_id:
        raise ValueError("未提供user_id参数")

    with get_db_context() as db:
        saved_cookie = get_douyin_cookie(db, user_id)
        if not saved_cookie:
            raise ValueError("未找到保存的Cookie")
            
    try:
        creators = db.query(DouyinCreator).filter(DouyinCreator.status == 1, DouyinCreator.auto_update == 1).all()
        # 初始化API客户端
        api = TikTokApi(cookie=saved_cookie)
        for creator in creators:
            sec_user_id = creator.sec_user_id
            # 获取创作者信息
            creator_info = api.get_user_info(sec_user_id=sec_user_id)
            if creator_info:
                # 更新创作者信息
                creator.nickname = creator_info.user.nickname
                creator.avatar_url = creator_info.user.avatar_larger.url_list[0]
                creator.unique_id = creator_info.user.unique_id
                creator.signature = creator_info.user.signature
                creator.ip_location = creator_info.user.ip_location
                creator.gender = creator_info.user.gender
                creator.follower_count = creator_info.user.follower_count
                creator.following_count = creator_info.user.following_count
                creator.aweme_count = creator_info.user.aweme_count
                creator.total_favorited = creator_info.user.total_favorited
                db.commit()
                logger.info(f"已更新创作者 {sec_user_id} 的信息")
            else:
                logger.error(f"获取创作者 {sec_user_id} 的信息失败")
            
    except Exception as e:
        logger.error(f"采集创作者信息失败: {str(e)}")
        raise
    
    logger.info(f"创作者信息采集完成")



if __name__ == "__main__":
    base_db.init_db()
    collect_creator_videos("MS4wLjABAAAAEyc7f8rfVXdpGZSd833RILo2zry0cEmYx5M7xXIW_U4-07BtwncUJsK3wiNrSt4a")

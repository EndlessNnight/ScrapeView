import os
import requests
import logging
import hashlib
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from app.scripts.douyin.schemas import DownloadTask, DownloadResult, DownloadTaskResult, CoverUrls
from app.crud.douyin import create_content_files_bulk
from app.schemas.douyin import DouyinContentFileCreate

logger = logging.getLogger(__name__)

class DownloadManager:
    def __init__(self, base_path: str = None, max_workers: int = 3):
        # 从环境变量获取下载路径，如果未设置则使用默认值 "downloads"
        self.base_path = base_path or os.getenv("DOUYIN_DOWNLOAD_PATH", "downloads")
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.headers = {
            "referer": 'https://www.douyin.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        }
    
    def _get_file_path(self, sec_user_id: str, aweme_id: str, file_type: str, ext: str = None) -> str:
        """生成文件保存路径
        Args:
            sec_user_id: 创作者ID
            aweme_id: 视频/图集ID
            file_type: 文件类型(video/cover/origin_cover/dynamic_cover/image_1/image_2等)
            ext: 文件扩展名
        Returns:
            str: 文件保存路径
        """
        if file_type == 'video':
            ext = ext or 'mp4'
        else:
            ext = ext or 'jpg'
            
        # 如果是图集图片，使用序号作为文件名
        if file_type.startswith('image_'):
            filename = f"{file_type}.{ext}"
        else:
            filename = f"{aweme_id}_{file_type}.{ext}"
            
        # 创建用户和视频/图集ID目录
        user_dir = os.path.join(self.base_path, sec_user_id)
        aweme_dir = os.path.join(user_dir, aweme_id)
        if not os.path.exists(aweme_dir):
            os.makedirs(aweme_dir)
            
        return os.path.join(aweme_dir, filename)
    
    def _download_file(self, url: str, file_path: str) -> DownloadTaskResult:
        """下载文件"""
        result = DownloadTaskResult(file_path=file_path)
        
        try:
            # 检查文件是否已存在
            if os.path.exists(file_path):
                # 获取文件大小
                file_size = os.path.getsize(file_path)
                # 读取文件内容计算哈希值
                with open(file_path, 'rb') as f:
                    content = f.read()
                    file_hash = hashlib.md5(content).hexdigest()
                
                result.success = True
                result.file_size = file_size
                result.file_hash = file_hash
                # logger.info(f"文件已存在，跳过下载: {file_path}")
                return result
            
            # 设置超时和重试次数
            response = requests.get(url, timeout=30, stream=True, headers=self.headers)
            if response.status_code != 200:
                result.error = f"下载请求失败，状态码: {response.status_code}"
                return result
            
            # 使用流式下载，避免内存占用过大
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
            
            result.file_size = len(content)
            result.file_hash = hashlib.md5(content).hexdigest()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(content)
            
            result.success = True
            # logger.info(f"文件下载成功: {file_path}")
            return result
                
        except Exception as e:
            result.error = f"下载文件失败: {str(e)}"
            logger.error(f"下载文件失败 {file_path}: {str(e)}")
            return result
    
    def _download_video_task(self, task: DownloadTask) -> DownloadResult:
        """下载单个视频任务"""
        result = DownloadResult(aweme_id=task.aweme_id)
        
        # 下载视频
        if task.video_urls:
            for url in task.video_urls:
                file_path = self._get_file_path(task.sec_user_id, task.aweme_id, 'video')
                download_result = self._download_file(url, file_path)
                if download_result.success:
                    result.video = download_result
                    break
                else:
                    result.video.error = download_result.error
        
        # 下载封面
        if task.cover_urls:
            for cover_info in task.cover_urls:
                file_path = self._get_file_path(task.sec_user_id, task.aweme_id, cover_info.cover_type)
                # 尝试下载列表中的每个URL直到成功
                for url in cover_info.url:
                    download_result = self._download_file(url, file_path)
                    if download_result.success:
                        download_result.cover_type = cover_info.cover_type
                        if cover_info.cover_type == 'cover':
                            result.cover = download_result
                        elif cover_info.cover_type == 'origin_cover':
                            result.origin_cover = download_result
                        elif cover_info.cover_type == 'dynamic_cover':
                            result.dynamic_cover = download_result
                        break
                    else:
                        if cover_info.cover_type == 'cover':
                            result.cover.error = download_result.error
                        elif cover_info.cover_type == 'origin_cover':
                            result.origin_cover.error = download_result.error
                        elif cover_info.cover_type == 'dynamic_cover':
                            result.dynamic_cover.error = download_result.error

        # 下载图片
        if task.image_urls:
            for index, url in enumerate(task.image_urls, 1):
                file_path = self._get_file_path(task.sec_user_id, task.aweme_id, f'image_{index}')
                download_result = self._download_file(url, file_path)
                if download_result.success:
                    download_result.image_index = index
                result.images.append(download_result)

        return result
    
    def batch_download_videos(self, tasks: List[DownloadTask]) -> List[DownloadResult]:
        """批量下载视频和图集
        Args:
            tasks: 下载任务列表
        Returns:
            下载结果列表
        """
        # 提交所有下载任务
        future_to_task = {
            self.executor.submit(self._download_video_task, task): task
            for task in tasks
        }
        
        # 收集结果
        results = []
        for future in as_completed(future_to_task):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                task = future_to_task[future]
                logger.error(f"下载任务执行失败 {task.aweme_id}: {str(e)}")
                results.append(DownloadResult(
                    aweme_id=task.aweme_id,
                    video=DownloadTaskResult(error=str(e)),
                    cover=DownloadTaskResult(error=str(e))
                ))
        
        return results

    def _convert_to_content_files(self, result: DownloadResult, content_id: Optional[int] = None) -> List[DouyinContentFileCreate]:
        """将下载结果转换为内容文件创建对象列表"""
        content_files = []
        
        # 如果content_id为None，则跳过创建内容文件记录
        if content_id is None:
            return []
        
        # 处理视频文件
        if result.video and result.video.success:
            download_status = "completed"
            error_message = None
            
            content_files.append(DouyinContentFileCreate(
                content_id=content_id,
                aweme_id=result.aweme_id,
                file_type="video",
                file_index=0,
                file_path=result.video.file_path,
                file_size=result.video.file_size,
                file_hash=result.video.file_hash,
                download_status=download_status,
                error_message=error_message
            ))
        
        # 处理封面文件
        for cover_type in ["cover", "origin_cover", "dynamic_cover"]:
            cover_result = getattr(result, cover_type, None)
            if cover_result and cover_result.success:
                content_files.append(DouyinContentFileCreate(
                    content_id=content_id,
                    aweme_id=result.aweme_id,
                    file_type=cover_type,
                    file_index=0,
                    file_path=cover_result.file_path,
                    file_size=cover_result.file_size,
                    file_hash=cover_result.file_hash,
                    download_status="completed",
                    error_message=None
                ))
        
        # 处理图片文件
        for image_result in result.images:
            if image_result.success:
                content_files.append(DouyinContentFileCreate(
                    content_id=content_id,
                    aweme_id=result.aweme_id,
                    file_type="image",
                    file_index=image_result.image_index,
                    file_path=image_result.file_path,
                    file_size=image_result.file_size,
                    file_hash=image_result.file_hash,
                    download_status="completed",
                    error_message=None
                ))
        
        return content_files

    def batch_download_videos_with_db(self, db: Session, tasks: List[DownloadTask]) -> Dict[str, List]:
        """批量下载视频和图集并保存文件记录到数据库
        
        Args:
            db: 数据库会话
            tasks: 下载任务列表
            
        Returns:
            Dict[str, List]: {
                "success": [成功创建的记录列表],
                "duplicates": [因aweme_id重复而未创建的记录列表],
                "failed": [下载失败的记录列表]
            }
        """
        # 执行下载
        download_results = self.batch_download_videos(tasks)
        
        # 转换为数据库记录
        content_files = []
        failed_results = []
        
        # 创建任务映射，用于查找content_id
        task_map = {task.aweme_id: task for task in tasks}
        
        for result in download_results:
            task = task_map.get(result.aweme_id)
            if not task:
                continue
                
            # 检查是否有内容ID
            content_id = task.content_id if hasattr(task, 'content_id') else None
            
            # 检查是否有成功下载的文件
            has_success = False
            if task.video_urls:  # 视频类型
                has_success = result.video and result.video.success
            elif task.image_urls:  # 图集类型
                has_success = any(img.success for img in result.images)
            
            if has_success:
                # 转换下载结果为内容文件记录
                content_files_create = self._convert_to_content_files(result, content_id)
                content_files.extend(content_files_create)
                
                # 如果是图集，更新内容的图片路径信息
                if task.image_urls and content_id:
                    from app.models.douyin import DouyinContent
                    content = db.query(DouyinContent).filter_by(id=content_id).first()
                    if content:
                        successful_images = [img for img in result.images if img.success]
                        if successful_images:
                            image_urls = content.image_urls or []
                            for img in successful_images:
                                # 将本地文件路径转换为URL格式，或者直接使用原始URL
                                # 这里假设我们只需要记录文件已下载的状态，不需要修改image_urls
                                pass
                            # 不需要更新image_urls，因为它应该已经包含了原始URL
                            # 如果需要记录本地路径，应该在DouyinContent模型中添加image_paths字段
            else:
                failed_results.append(result)
        
        try:
            # 批量创建数据库记录
            db_result = create_content_files_bulk(db, content_files) if content_files else {"created": [], "skipped": []}
            
            # 提交事务
            db.commit()
            
            return {
                "success": db_result["created"],
                "duplicates": db_result["skipped"],
                "failed": failed_results
            }
        except Exception as e:
            logger.error(f"保存文件记录失败: {str(e)}")
            db.rollback()
            # 将所有记录标记为失败
            return {
                "success": [],
                "duplicates": [],
                "failed": download_results
            }

if __name__ == "__main__":
    from app.db.session import base_db
    base_db.init_db()
    # 创建下载任务
    tasks = [
        DownloadTask(
            sec_user_id='MS4wLjABAAAAEyc7f8rfVXdpGZSd833RILo2zry0cEmYx5M7xXIW_U4-07BtwncUJsK3wiNrSt4a',
            aweme_id='7425582833831316773',
            video_urls=[
                "https://v5-dy-o-abtest.zjcdn.com/449957becedc0ed91dadd5f3225b2943/67b9691c/video/tos/cn/tos-cn-ve-15/ocfz5jeoA1BhC4WiZIiwVI1RAAhzEgB4nYKDvA/?a=6383&ch=10010&cr=3&dr=0&lr=all&cd=0%7C0%7C0%7C3&cv=1&br=1057&bt=1057&cs=0&ds=4&ft=CZcaELOtDDhNJFVQ9wFkg9ahd.LlMeTR3-ApQX&mime_type=video_mp4&qs=0&rc=PDg6ZGg5M2U6aTk5Z2hpZ0BpM3JkdnI5cmRpdjMzNGkzM0AvMmBfMS0xNjQxYl41YjEwYSMtM2xrMmRzZDNgLS1kLTBzcw%3D%3D&btag=c0000e00008000&cc=46&cquery=100B_100x_100z_100o_101r&dy_q=1740193511&feature_id=46a7bb47b4fd1280f3d3825bf2b29388&l=20250222110511560D9E04C367236827B6&req_cdn_type=",
                "https://v3-dy-o.zjcdn.com/5a39a75b7937a16b1bb177a714e149a9/67b9691c/video/tos/cn/tos-cn-ve-15/ocfz5jeoA1BhC4WiZIiwVI1RAAhzEgB4nYKDvA/?a=6383&ch=10010&cr=3&dr=0&lr=all&cd=0%7C0%7C0%7C3&cv=1&br=1057&bt=1057&cs=0&ds=4&ft=CZcaELOtDDhNJFVQ9wFkg9ahd.LlMeTR3-ApQX&mime_type=video_mp4&qs=0&rc=PDg6ZGg5M2U6aTk5Z2hpZ0BpM3JkdnI5cmRpdjMzNGkzM0AvMmBfMS0xNjQxYl41YjEwYSMtM2xrMmRzZDNgLS1kLTBzcw%3D%3D&btag=c0000e00008000&cc=1f&cquery=101r_100B_100x_100z_100o&dy_q=1740193511&feature_id=46a7bb47b4fd1280f3d3825bf2b29388&l=20250222110511560D9E04C367236827B6&req_cdn_type=",
                "https://www.douyin.com/aweme/v1/play/?video_id=v0300fg10000cs6fgavog65onsoa6o00&line=0&file_id=3d4fee8da6e64f779b40064ebac75529&sign=c2cd4d294c3bf4728cef1a4503188251&is_play_url=1&source=PackSourceEnum_PUBLISH"
            ],
            cover_urls=[
                CoverUrls(cover_type="cover", url=["https://p3-pc-sign.douyinpic.com/tos-cn-p-0015/oUZmAMGE3QcbLgGBrMeE2fXJEiwnefDFAICAQI~tplv-dy-cropcenter:323:430.jpeg?lk3s=138a59ce&x-expires=2055553200&x-signature=WbRPDSdxL%2FNoMueYgC%2FxYKmhYsg%3D&from=327834062&s=PackSourceEnum_PUBLISH&se=true&sh=323_430&sc=cover&biz_tag=pcweb_cover&l=20250222110511560D9E04C367236827B6"]),
                CoverUrls(cover_type="origin_cover", url=["https://p3-pc-sign.douyinpic.com/tos-cn-p-0015/oA3MCK8MMgFy2NcDfeQAwMgfZEEAIQBdXCfXgA~tplv-dy-360p.jpeg?lk3s=138a59ce&x-expires=1741402800&x-signature=%2Btqa14WQNy0YpnjoZzzSq9P1vDY%3D&from=327834062&s=PackSourceEnum_PUBLISH&se=false&sc=origin_cover&biz_tag=pcweb_cover&l=20250222110511560D9E04C367236827B6"]),
                CoverUrls(cover_type="dynamic_cover", url=["https://p9-pc-sign.douyinpic.com/obj/tos-cn-p-0015/ooJfZGMOQAMXfwBDiC8IrGB3fQg2ARLFcZEmAe?lk3s=138a59ce&x-expires=1741402800&x-signature=fxLk64xtzHaO5NUFfelPik8PQX4%3D&from=327834062_large&s=PackSourceEnum_PUBLISH&se=false&sc=dynamic_cover&biz_tag=pcweb_cover&l=20250222110511560D9E04C367236827B6"])
            ]
        )
    ]

    # 创建下载管理器并执行下载
    downloader = DownloadManager(max_workers=3)
    with base_db.get_db() as session:
        results = downloader.batch_download_videos_with_db(session, tasks)
        print(f"成功: {len(results['success'])} 个")
        print(f"重复: {len(results['duplicates'])} 个")
        print(f"失败: {len(results['failed'])} 个")
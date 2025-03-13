import os
import hashlib
import uuid
import logging
import mimetypes
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from typing import Tuple, Optional

import aiohttp
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
import app.crud.pt_site as crud
from app.schemas.pt_site import ProxyImageCreate


def _check_existing_image(db: Session, url: str) -> Tuple[Optional[str], Optional[str], Optional[any]]:
    """检查是否存在相同URL的图片
    
    Args:
        db: 数据库会话
        url: 图片URL
        
    Returns:
        tuple: (文件路径, 文件类型, 数据库图片对象)
    """
    existing_image = crud.get_proxy_image_by_url(db, url)
    if existing_image:
        file_path = os.path.join(existing_image.local_path, existing_image.file_name)
        if os.path.exists(file_path):
            return file_path, existing_image.mime_type or "image/jpeg", existing_image
    return None, None, None


async def _download_with_aiohttp(url: str, timeout: int = 10) -> Tuple[bytes, str]:
    """使用aiohttp下载图片
    
    Args:
        url: 图片URL
        timeout: 超时时间（秒）
        
    Returns:
        tuple: (图片内容, 内容类型)
        
    Raises:
        HTTPException: 当下载失败时
    """
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    
    # 设置代理
    proxy_auth = None
    proxy = None
    if settings.HTTP_PROXY or settings.HTTPS_PROXY:
        parsed_url = urlparse(url)
        proxy_url = None
        if parsed_url.scheme == 'https' and settings.HTTPS_PROXY:
            proxy_url = settings.HTTPS_PROXY
        elif parsed_url.scheme == 'http' and settings.HTTP_PROXY:
            proxy_url = settings.HTTP_PROXY
            
        # 检查是否在NO_PROXY列表中
        if settings.NO_PROXY:
            no_proxy_list = [x.strip() for x in settings.NO_PROXY.split(',')]
            if any(parsed_url.netloc.endswith(domain) for domain in no_proxy_list):
                proxy_url = None
        if proxy_url:
            # 解析代理URL
            proxy_parsed = urlparse(proxy_url)
            if proxy_parsed.username and proxy_parsed.password:
                proxy_auth = aiohttp.BasicAuth(proxy_parsed.username, proxy_parsed.password)
                # 重构代理URL，移除认证信息
                proxy = f"{proxy_parsed.scheme}://{proxy_parsed.hostname}:{proxy_parsed.port}"
            else:
                proxy = proxy_url
    
    try:
        async with aiohttp.ClientSession(timeout=timeout_obj) as session:
            async with session.get(url, proxy=proxy, proxy_auth=proxy_auth) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"使用aiohttp下载图片失败: HTTP {response.status}"
                    )
                
                content = await response.read()
                content_type = _get_content_type(response.headers.get("Content-Type", ""), url)
                return content, content_type
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"使用aiohttp下载图片失败: {str(e)}"
        )


def _download_with_cloudscraper(url: str, timeout: int = 10) -> Tuple[bytes, str]:
    """使用cloudscraper下载图片
    
    Args:
        url: 图片URL
        timeout: 超时时间（秒）
        
    Returns:
        tuple: (图片内容, 内容类型)
        
    Raises:
        HTTPException: 当下载失败时
    """
    try:
        import cloudscraper
        import requests.exceptions
        
        # 设置代理
        proxies = {}
        if settings.HTTP_PROXY:
            proxies['http'] = settings.HTTP_PROXY
        if settings.HTTPS_PROXY:
            proxies['https'] = settings.HTTPS_PROXY
            
        # 检查是否在NO_PROXY列表中
        if settings.NO_PROXY and (proxies.get('http') or proxies.get('https')):
            parsed_url = urlparse(url)
            no_proxy_list = [x.strip() for x in settings.NO_PROXY.split(',')]
            if any(parsed_url.netloc.endswith(domain) for domain in no_proxy_list):
                proxies = {}
        
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        parsed_url = urlparse(url)
        headers = {
            "Referer": f"{parsed_url.scheme}://{parsed_url.netloc}",
            "Origin": f"{parsed_url.scheme}://{parsed_url.netloc}",
            "Host": parsed_url.netloc
        }
        
        response = scraper.get(url, headers=headers, timeout=timeout, proxies=proxies)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"使用cloudscraper下载图片失败: HTTP {response.status_code}"
            )
        
        content = response.content
        content_type = _get_content_type(response.headers.get("content-type", ""), url)
        return content, content_type
        
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="下载图片失败，cloudscraper未安装"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"下载图片超时，超过{timeout}秒"
        )
    except Exception as scraper_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"下载图片失败: {str(scraper_error)}"
        )


def _get_content_type(content_type: str, url: str) -> str:
    """获取图片的内容类型
    
    Args:
        content_type: 响应头中的内容类型
        url: 图片URL
        
    Returns:
        str: 内容类型
    """
    if not content_type or "image" not in content_type:
        parsed_url = urlparse(url)
        path = parsed_url.path
        ext = os.path.splitext(path)[1]
        if ext:
            content_type = mimetypes.guess_type(ext)[0] or "image/jpeg"
        else:
            content_type = "image/jpeg"
    return content_type


def _save_image(content: bytes, url: str, storage_path: Path, content_type: str) -> str:
    """保存图片到本地
    
    Args:
        content: 图片内容
        url: 图片URL
        storage_path: 存储路径
        content_type: 内容类型
        
    Returns:
        str: 文件名
    """
    url_hash = hashlib.md5(url.encode()).hexdigest()
    unique_id = str(uuid.uuid4())[:8]
    ext = mimetypes.guess_extension(content_type) or ".jpg"
    file_name = f"{url_hash}_{unique_id}{ext}"
    
    file_path = os.path.join(storage_path, file_name)
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_name


async def download_and_store_image(url: str, db: Session) -> Tuple[str, str, any]:
    """下载和存储图片
    
    Args:
        url: 图片URL
        db: 数据库会话
        
    Returns:
        tuple: (文件路径, 文件类型, 数据库图片对象)
    """
    # 检查已存在的图片
    file_path, mime_type, existing_image = _check_existing_image(db, url)
    if file_path:
        return file_path, mime_type, existing_image
    
    # 确保存储目录存在
    storage_path = Path(settings.IMAGES_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # 尝试使用aiohttp下载
    try:
        content, content_type = await _download_with_aiohttp(url)
    except (asyncio.TimeoutError, HTTPException) as e:
        logging.warning(f"使用aiohttp下载图片失败: {str(e)}，将尝试使用cloudscraper")
        # 使用cloudscraper作为备选方案
        content, content_type = _download_with_cloudscraper(url)
    
    # 保存图片
    file_name = _save_image(content, url, storage_path, content_type)
    
    # 创建数据库记录
    image_create = ProxyImageCreate(original_url=url)
    db_image = crud.create_proxy_image(
        db=db,
        image=image_create,
        local_path=str(storage_path),
        file_name=file_name,
        file_size=len(content),
        mime_type=content_type
    )
    
    file_path = os.path.join(storage_path, file_name)
    return file_path, content_type, db_image 

import cloudscraper
import os
import logging
from pathlib import Path
from urllib.parse import urlparse

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

def test_cloudscraper_download():
    """测试使用 cloudscraper 下载图片"""
    # 目标URL
    url = "https://img.pterclub.com/images/2023/12/25/12r5gl0.jpg"
    
    # 创建保存图片的目录
    save_dir = Path("tests/test_downloads")
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / "cloudscraper_test_image.jpg"
    
    try:
        # 创建一个cloudscraper实例
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # 从URL中提取域名，用于设置请求头
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # 设置请求头
        headers = {
            "Referer": origin,
            "Origin": origin,
            "Host": host
        }
        
        logging.debug(f"开始请求URL: {url}")
        logging.debug(f"使用的请求头: {headers}")
        
        # 发送请求
        response = scraper.get(url, headers=headers)
        logging.debug(f"响应状态码: {response.status_code}")
        logging.debug(f"响应头: {response.headers}")
        
        if response.status_code == 200:
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logging.error(f"响应不是图片，而是: {content_type}")
                logging.error(f"响应内容: {response.text[:500]}")  # 只打印前500个字符
                raise ValueError(f"响应不是图片: {content_type}")
            
            # 保存图片
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            # 验证文件
            file_size = os.path.getsize(save_path)
            logging.debug(f"保存的文件大小: {file_size} bytes")
            
            assert os.path.exists(save_path), "文件未创建"
            assert file_size > 0, "文件大小为0"
            print(f"图片已成功下载到: {save_path}")
            print(f"文件大小: {file_size} bytes")
            return True
        else:
            logging.error(f"错误响应内容: {response.text}")
            raise ValueError(f"下载失败，状态码: {response.status_code}")
            
    except Exception as e:
        logging.error(f"发生错误: {str(e)}")
        raise e
    finally:
        # 测试完成后清理文件
        if save_path.exists():
            save_path.unlink()
        if save_dir.exists() and len(list(save_dir.iterdir())) == 0:
            save_dir.rmdir()

if __name__ == "__main__":
    test_cloudscraper_download() 
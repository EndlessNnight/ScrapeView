#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CloudflareDownloader使用示例

此脚本展示了如何使用CloudflareDownloader类下载受Cloudflare保护的资源
"""

import os
import sys
import logging
from pathlib import Path

# 导入CloudflareDownloader类
try:
    from cloudflare_downloader import CloudflareDownloader
except ImportError:
    print("找不到cloudflare_downloader.py，请确保它与此脚本在同一目录下")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Example')

def main():
    """主函数"""
    # 初始化下载器
    downloader = CloudflareDownloader(
        base_url="https://kamept.com",
        download_dir="downloads",
        cookies_dir="cookies"
    )
    
    # 目标URL
    url = "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg.thumb.jpg"
    
    # 检查是否已有保存的cookies
    cookies = downloader.load_cookies()
    if cookies:
        logger.info("找到已保存的cookies，尝试使用cookies下载")
        result = downloader.download(url, method="cookies")
        if result:
            logger.info(f"使用cookies下载成功: {result}")
            return
        else:
            logger.warning("使用cookies下载失败，尝试其他方法")
    
    # 使用Selenium方法
    logger.info("使用Selenium方法下载")
    
    # 初始化WebDriver
    driver = downloader.init_selenium_driver(
        use_undetected=True,  # 使用undetected_chromedriver
        use_stealth=True,     # 使用selenium-stealth
        headless=False        # 不使用无头模式，以便手动完成验证
    )
    
    if not driver:
        logger.error("初始化WebDriver失败")
        return
    
    try:
        # 先访问网站首页，通过Cloudflare验证
        logger.info("访问网站首页，通过Cloudflare验证")
        if downloader.verify_cloudflare(wait_for_user=True):
            logger.info("Cloudflare验证成功，开始下载图片")
            
            # 下载图片
            result = downloader.download_with_selenium(
                url=url,
                verify_first=False,  # 已经验证过了，不需要再次验证
                save_screenshot=True  # 保存页面截图
            )
            
            if result:
                logger.info(f"下载成功: {result}")
                
                # 尝试使用保存的cookies再次下载
                logger.info("尝试使用刚才保存的cookies再次下载")
                cookies_result = downloader.download(url, method="cookies")
                if cookies_result:
                    logger.info(f"使用cookies再次下载成功: {cookies_result}")
                else:
                    logger.warning("使用cookies再次下载失败")
            else:
                logger.error("下载失败")
        else:
            logger.error("Cloudflare验证失败")
    finally:
        # 关闭WebDriver
        downloader.close_driver()

def batch_download():
    """批量下载示例"""
    # 初始化下载器
    downloader = CloudflareDownloader(
        base_url="https://kamept.com",
        download_dir="downloads/batch",
        cookies_dir="cookies"
    )
    
    # 目标URL列表
    urls = [
        "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg.thumb.jpg",
        "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg",
        # 添加更多URL...
    ]
    
    # 检查是否已有保存的cookies
    cookies = downloader.load_cookies()
    if not cookies:
        # 如果没有cookies，使用Selenium获取
        logger.info("未找到cookies，使用Selenium获取")
        driver = downloader.init_selenium_driver(use_undetected=True, headless=False)
        if driver:
            try:
                downloader.verify_cloudflare(wait_for_user=True)
            finally:
                downloader.close_driver()
        else:
            logger.error("初始化WebDriver失败")
            return
    
    # 使用cookies批量下载
    success_count = 0
    for i, url in enumerate(urls):
        logger.info(f"下载第{i+1}/{len(urls)}个文件: {url}")
        result = downloader.download(url, method="cookies")
        if result:
            logger.info(f"下载成功: {result}")
            success_count += 1
        else:
            logger.error(f"下载失败: {url}")
    
    logger.info(f"批量下载完成，成功: {success_count}/{len(urls)}")

if __name__ == "__main__":
    print("=== CloudflareDownloader使用示例 ===")
    print("1. 单个文件下载")
    print("2. 批量下载")
    
    choice = input("请选择示例 (1/2): ")
    
    if choice == "1":
        main()
    elif choice == "2":
        batch_download()
    else:
        print("无效的选择") 
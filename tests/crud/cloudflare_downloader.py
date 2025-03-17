#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cloudflare下载器 - 用于下载受Cloudflare保护的资源

此模块提供了多种方法来绕过Cloudflare保护并下载资源，包括：
1. 使用cloudscraper库
2. 使用预设的cookies
3. 使用Selenium和undetected_chromedriver
4. 使用curl命令
5. 使用保存的cookies
6. 使用selenium-stealth

作者: AI助手
日期: 2023-05-11
"""

import os
import json
import time
import base64
import logging
import requests
from pathlib import Path
from urllib.parse import urlparse, urljoin

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CloudflareDownloader')

class CloudflareDownloader:
    """用于下载受Cloudflare保护的资源的下载器"""
    
    def __init__(self, base_url=None, download_dir="downloads", cookies_dir="cookies"):
        """
        初始化CloudflareDownloader
        
        参数:
            base_url (str): 网站的基础URL，例如 "https://kamept.com"
            download_dir (str): 下载文件保存的目录
            cookies_dir (str): 保存cookies的目录
        """
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.cookies_dir = Path(cookies_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.cookies_dir.mkdir(parents=True, exist_ok=True)
        self.driver = None
        self.cookies = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        
        logger.info(f"CloudflareDownloader初始化完成，下载目录: {self.download_dir}, cookies目录: {self.cookies_dir}")
    
    def _get_domain_from_url(self, url):
        """从URL中提取域名"""
        parsed_url = urlparse(url)
        return parsed_url.netloc
    
    def _get_filename_from_url(self, url):
        """从URL中提取文件名"""
        parsed_url = urlparse(url)
        return os.path.basename(parsed_url.path)
    
    def _get_cookies_filename(self, url):
        """根据URL生成cookies文件名"""
        domain = self._get_domain_from_url(url)
        return self.cookies_dir / f"{domain}_cookies.json"
    
    def save_cookies(self, cookies, url=None):
        """
        保存cookies到文件
        
        参数:
            cookies (list/dict): 要保存的cookies
            url (str): 相关的URL，用于生成文件名
        """
        if url is None and self.base_url is None:
            raise ValueError("必须提供URL或在初始化时设置base_url")
        
        target_url = url or self.base_url
        cookies_file = self._get_cookies_filename(target_url)
        
        try:
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=4)
            logger.info(f"Cookies已保存到: {cookies_file}")
            return True
        except Exception as e:
            logger.error(f"保存cookies失败: {str(e)}")
            return False
    
    def load_cookies(self, url=None):
        """
        从文件加载cookies
        
        参数:
            url (str): 相关的URL，用于生成文件名
            
        返回:
            dict/list: 加载的cookies，如果文件不存在则返回None
        """
        if url is None and self.base_url is None:
            raise ValueError("必须提供URL或在初始化时设置base_url")
        
        target_url = url or self.base_url
        cookies_file = self._get_cookies_filename(target_url)
        
        if not os.path.exists(cookies_file):
            logger.warning(f"Cookies文件不存在: {cookies_file}")
            return None
        
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            logger.info(f"已从{cookies_file}加载cookies")
            self.cookies = cookies
            return cookies
        except Exception as e:
            logger.error(f"加载cookies失败: {str(e)}")
            return None
    
    def download_with_cloudscraper(self, url, save_path=None, **kwargs):
        """
        使用cloudscraper库下载资源
        
        参数:
            url (str): 要下载的资源URL
            save_path (str): 保存文件的路径，如果为None则自动生成
            **kwargs: 传递给cloudscraper.get()的其他参数
            
        返回:
            str: 保存的文件路径，如果下载失败则返回None
        """
        try:
            import cloudscraper
        except ImportError:
            logger.error("缺少cloudscraper库，请安装: pip install cloudscraper")
            return None
        
        if save_path is None:
            domain = self._get_domain_from_url(url)
            filename = self._get_filename_from_url(url)
            save_dir = self.download_dir / domain
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / filename
        else:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"使用cloudscraper下载: {url}")
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, **kwargs)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"文件已保存到: {save_path}")
                return str(save_path)
            else:
                logger.error(f"下载失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"使用cloudscraper下载时出错: {str(e)}")
            return None
    
    def download_with_cookies(self, url, cookies=None, save_path=None, **kwargs):
        """
        使用预设的cookies下载资源
        
        参数:
            url (str): 要下载的资源URL
            cookies (dict): 用于请求的cookies，如果为None则使用已加载的cookies
            save_path (str): 保存文件的路径，如果为None则自动生成
            **kwargs: 传递给requests.get()的其他参数
            
        返回:
            str: 保存的文件路径，如果下载失败则返回None
        """
        if cookies is None:
            cookies = self.cookies
            if cookies is None:
                cookies = self.load_cookies(url)
                if cookies is None:
                    logger.error("没有可用的cookies，请先获取cookies")
                    return None
        
        if save_path is None:
            domain = self._get_domain_from_url(url)
            filename = self._get_filename_from_url(url)
            save_dir = self.download_dir / domain
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / f"cookies_{filename}"
        else:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果cookies是列表格式，转换为字典
        if isinstance(cookies, list):
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        else:
            cookies_dict = cookies
        
        # 设置请求头
        headers = {
            "User-Agent": self.user_agent,
            "Referer": self.base_url or urlparse(url).scheme + "://" + urlparse(url).netloc
        }
        
        # 合并headers和kwargs中的headers
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        try:
            logger.info(f"使用cookies下载: {url}")
            response = requests.get(url, headers=headers, cookies=cookies_dict, **kwargs)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"文件已保存到: {save_path}")
                return str(save_path)
            else:
                logger.error(f"下载失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"使用cookies下载时出错: {str(e)}")
            return None
    
    def init_selenium_driver(self, use_undetected=True, use_stealth=False, headless=False):
        """
        初始化Selenium WebDriver
        
        参数:
            use_undetected (bool): 是否使用undetected_chromedriver
            use_stealth (bool): 是否使用selenium-stealth
            headless (bool): 是否使用无头模式
            
        返回:
            WebDriver: 初始化的WebDriver对象
        """
        try:
            if use_undetected:
                try:
                    import undetected_chromedriver as uc
                    logger.info("使用undetected_chromedriver初始化WebDriver")
                    
                    options = uc.ChromeOptions()
                    if headless:
                        options.add_argument("--headless")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--window-size=1920,1080")
                    
                    self.driver = uc.Chrome(options=options)
                except ImportError:
                    logger.error("缺少undetected_chromedriver库，请安装: pip install undetected-chromedriver")
                    use_undetected = False
            
            if not use_undetected:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                
                logger.info("使用标准Selenium初始化WebDriver")
                
                options = Options()
                if headless:
                    options.add_argument("--headless")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--window-size=1920,1080")
                
                # 添加反检测选项
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                self.driver = webdriver.Chrome(options=options)
                
                # 应用stealth设置
                if use_stealth:
                    try:
                        import selenium_stealth
                        logger.info("应用selenium-stealth设置")
                        
                        selenium_stealth.stealth(
                            self.driver,
                            languages=["zh-CN", "zh", "en-US", "en"],
                            vendor="Google Inc.",
                            platform="Win32",
                            webgl_vendor="Intel Inc.",
                            renderer="Intel Iris OpenGL Engine",
                            fix_hairline=True,
                        )
                    except ImportError:
                        logger.error("缺少selenium-stealth库，请安装: pip install selenium-stealth")
            
            logger.info("WebDriver初始化完成")
            return self.driver
        except Exception as e:
            logger.error(f"初始化WebDriver失败: {str(e)}")
            return None
    
    def close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver已关闭")
            except Exception as e:
                logger.error(f"关闭WebDriver时出错: {str(e)}")
            finally:
                self.driver = None
    
    def verify_cloudflare(self, url=None, wait_for_user=True, timeout=30):
        """
        访问网站并通过Cloudflare验证
        
        参数:
            url (str): 要访问的URL，如果为None则使用base_url
            wait_for_user (bool): 是否等待用户手动完成验证
            timeout (int): 等待验证完成的超时时间（秒）
            
        返回:
            bool: 验证是否成功
        """
        if self.driver is None:
            logger.error("WebDriver未初始化，请先调用init_selenium_driver()")
            return False
        
        if url is None and self.base_url is None:
            raise ValueError("必须提供URL或在初始化时设置base_url")
        
        target_url = url or self.base_url
        
        try:
            logger.info(f"访问URL: {target_url}")
            self.driver.get(target_url)
            
            if wait_for_user:
                logger.info("请在浏览器中完成人机验证（如果出现），然后按Enter键继续...")
                input()
            else:
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                logger.info(f"等待Cloudflare验证完成，超时时间: {timeout}秒")
                try:
                    WebDriverWait(self.driver, timeout).until_not(
                        EC.title_contains("Just a moment")
                    )
                    logger.info("Cloudflare验证已自动通过")
                except:
                    logger.warning("等待超时，但可能已经通过验证")
            
            # 获取并保存cookies
            cookies = self.driver.get_cookies()
            self.cookies = cookies
            self.save_cookies(cookies, target_url)
            
            return True
        except Exception as e:
            logger.error(f"Cloudflare验证失败: {str(e)}")
            return False
    
    def download_with_selenium(self, url, save_path=None, verify_first=True, save_screenshot=True):
        """
        使用Selenium下载资源
        
        参数:
            url (str): 要下载的资源URL
            save_path (str): 保存文件的路径，如果为None则自动生成
            verify_first (bool): 是否先进行Cloudflare验证
            save_screenshot (bool): 是否保存页面截图
            
        返回:
            str: 保存的文件路径，如果下载失败则返回None
        """
        if self.driver is None:
            logger.error("WebDriver未初始化，请先调用init_selenium_driver()")
            return None
        
        if save_path is None:
            domain = self._get_domain_from_url(url)
            filename = self._get_filename_from_url(url)
            save_dir = self.download_dir / domain
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / f"selenium_{filename}"
        else:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 如果需要先进行验证
            if verify_first and self.base_url:
                self.verify_cloudflare(self.base_url)
            
            # 访问图片URL
            logger.info(f"访问资源URL: {url}")
            self.driver.get(url)
            
            # 等待资源加载完成
            time.sleep(5)
            
            # 保存页面截图
            if save_screenshot:
                screenshot_path = save_path.with_suffix('.png')
                self.driver.save_screenshot(str(screenshot_path))
                logger.info(f"页面截图已保存到: {screenshot_path}")
            
            # 尝试获取图片元素并下载
            try:
                from selenium.webdriver.common.by import By
                
                # 找到图片元素
                img_element = self.driver.find_element(By.TAG_NAME, "img")
                
                # 获取图片的src属性
                img_src = img_element.get_attribute("src")
                
                if img_src.startswith("data:image"):
                    # 如果是base64编码的图片
                    img_data = img_src.split(",")[1]
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(img_data))
                    logger.info(f"Base64图片已保存到: {save_path}")
                    return str(save_path)
                else:
                    # 如果是URL，使用requests下载
                    return self.download_with_cookies(img_src, self.cookies, save_path)
            except Exception as e:
                logger.error(f"获取图片元素失败: {str(e)}")
                return str(screenshot_path) if save_screenshot else None
        except Exception as e:
            logger.error(f"使用Selenium下载时出错: {str(e)}")
            return None
    
    def download_with_curl(self, url, cookies=None, save_path=None):
        """
        使用curl命令下载资源
        
        参数:
            url (str): 要下载的资源URL
            cookies (dict): 用于请求的cookies，如果为None则使用已加载的cookies
            save_path (str): 保存文件的路径，如果为None则自动生成
            
        返回:
            str: 保存的文件路径，如果下载失败则返回None
        """
        if cookies is None:
            cookies = self.cookies
            if cookies is None:
                cookies = self.load_cookies(url)
                if cookies is None:
                    logger.error("没有可用的cookies，请先获取cookies")
                    return None
        
        if save_path is None:
            domain = self._get_domain_from_url(url)
            filename = self._get_filename_from_url(url)
            save_dir = self.download_dir / domain
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / f"curl_{filename}"
        else:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果cookies是列表格式，转换为字典
        if isinstance(cookies, list):
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            cookies_str = "; ".join([f"{name}={value}" for name, value in cookies_dict.items()])
        else:
            cookies_str = "; ".join([f"{name}={value}" for name, value in cookies.items()])
        
        # 构建curl命令
        referer = self.base_url or urlparse(url).scheme + "://" + urlparse(url).netloc
        curl_cmd = [
            "curl",
            "-s",
            "-o", str(save_path),
            "-L",
            "-A", f'"{self.user_agent}"',
            "-e", f'"{referer}"',
            "-b", f'"{cookies_str}"',
            f'"{url}"'
        ]
        
        cmd = " ".join(curl_cmd)
        
        try:
            import subprocess
            logger.info(f"使用curl下载: {url}")
            logger.debug(f"执行命令: {cmd}")
            
            result = subprocess.run(cmd, shell=True, check=True)
            
            if result.returncode == 0 and os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                logger.info(f"文件已保存到: {save_path}")
                return str(save_path)
            else:
                logger.error("curl命令执行失败或下载的文件为空")
                return None
        except Exception as e:
            logger.error(f"使用curl下载时出错: {str(e)}")
            return None
    
    def download(self, url, method="auto", save_path=None, **kwargs):
        """
        下载资源，自动选择或指定下载方法
        
        参数:
            url (str): 要下载的资源URL
            method (str): 下载方法，可选值: "auto", "cloudscraper", "cookies", "selenium", "curl"
            save_path (str): 保存文件的路径，如果为None则自动生成
            **kwargs: 传递给具体下载方法的其他参数
            
        返回:
            str: 保存的文件路径，如果下载失败则返回None
        """
        if method == "auto":
            # 尝试使用cookies下载
            cookies = self.cookies or self.load_cookies(url)
            if cookies:
                result = self.download_with_cookies(url, cookies, save_path, **kwargs)
                if result:
                    return result
            
            # 尝试使用cloudscraper下载
            try:
                import cloudscraper
                result = self.download_with_cloudscraper(url, save_path, **kwargs)
                if result:
                    return result
            except ImportError:
                logger.warning("缺少cloudscraper库，跳过此方法")
            
            # 尝试使用Selenium下载
            if self.driver is None:
                self.init_selenium_driver(use_undetected=True, use_stealth=True, headless=False)
            
            if self.driver:
                result = self.download_with_selenium(url, save_path, **kwargs)
                self.close_driver()
                if result:
                    return result
            
            # 尝试使用curl下载
            result = self.download_with_curl(url, cookies, save_path)
            if result:
                return result
            
            logger.error("所有下载方法都失败")
            return None
        
        elif method == "cloudscraper":
            return self.download_with_cloudscraper(url, save_path, **kwargs)
        
        elif method == "cookies":
            cookies = kwargs.pop("cookies", None) or self.cookies or self.load_cookies(url)
            return self.download_with_cookies(url, cookies, save_path, **kwargs)
        
        elif method == "selenium":
            if self.driver is None:
                use_undetected = kwargs.pop("use_undetected", True)
                use_stealth = kwargs.pop("use_stealth", False)
                headless = kwargs.pop("headless", False)
                self.init_selenium_driver(use_undetected, use_stealth, headless)
            
            try:
                return self.download_with_selenium(url, save_path, **kwargs)
            finally:
                if kwargs.pop("close_driver", True):
                    self.close_driver()
        
        elif method == "curl":
            cookies = kwargs.pop("cookies", None) or self.cookies or self.load_cookies(url)
            return self.download_with_curl(url, cookies, save_path)
        
        else:
            logger.error(f"不支持的下载方法: {method}")
            return None


# 使用示例
if __name__ == "__main__":
    # 初始化下载器
    downloader = CloudflareDownloader(
        base_url="https://kamept.com",
        download_dir="downloads",
        cookies_dir="cookies"
    )
    
    # 目标URL
    url = "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg.thumb.jpg"
    
    # 方法1：使用cloudscraper
    print("\n尝试方法1：使用cloudscraper")
    result = downloader.download(url, method="cloudscraper")
    if result:
        print(f"下载成功: {result}")
    else:
        print("下载失败")
    
    # 方法2：使用Selenium
    print("\n尝试方法2：使用Selenium")
    result = downloader.download(url, method="selenium", use_undetected=True, headless=False)
    if result:
        print(f"下载成功: {result}")
    else:
        print("下载失败")
    
    # 方法3：使用保存的cookies
    print("\n尝试方法3：使用保存的cookies")
    result = downloader.download(url, method="cookies")
    if result:
        print(f"下载成功: {result}")
    else:
        print("下载失败")
    
    # 方法4：自动选择最佳方法
    print("\n尝试方法4：自动选择最佳方法")
    result = downloader.download(url)
    if result:
        print(f"下载成功: {result}")
    else:
        print("下载失败") 
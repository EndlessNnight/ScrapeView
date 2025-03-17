import cloudscraper
import os
import logging
import time
import requests
from pathlib import Path
from urllib.parse import urlparse

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

def test_download_kamept_image():
    """测试从Kamept网站下载需要通过Cloudflare保护的图片"""
    # 目标URL
    url = "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg.thumb.jpg"
    
    # 创建保存图片的目录
    save_dir = Path("downloads/kamept")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 从URL中提取文件名
    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    save_path = save_dir / file_name
    
    try:
        # 创建一个cloudscraper实例，模拟Chrome浏览器
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10  # 增加延迟，避免被识别为机器人
        )
        
        # 从URL中提取域名，用于设置请求头
        host = parsed_url.netloc
        origin = f"https://{host}"
        referer = f"https://{host}/"
        
        # 设置请求头，模拟真实浏览器
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": referer,
            "Origin": origin,
            "Host": host,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-origin",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        }
        
        logging.debug(f"开始请求URL: {url}")
        logging.debug(f"使用的请求头: {headers}")
        
        # 先访问网站首页，获取cookies
        home_url = f"https://{host}/"
        logging.debug(f"先访问首页: {home_url}")
        home_response = scraper.get(home_url, headers=headers)
        logging.debug(f"首页响应状态码: {home_response.status_code}")
        
        # 等待一段时间，模拟人类行为
        time.sleep(3)
        
        # 发送请求下载图片
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
            logging.error(f"错误响应内容: {response.text[:500]}")
            raise ValueError(f"下载失败，状态码: {response.status_code}")
            
    except Exception as e:
        logging.error(f"发生错误: {str(e)}")
        raise e

def test_download_with_cookies():
    """使用保存的cookies下载需要通过Cloudflare保护的图片"""
    # 目标URL
    url = "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg.thumb.jpg"
    
    # 创建保存图片的目录
    save_dir = Path("downloads/kamept")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 从URL中提取文件名
    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    save_path = save_dir / f"cookies_{file_name}"
    
    try:
        # 创建一个cloudscraper实例
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # 手动设置cookies（这些cookies需要从浏览器中获取）
        # 注意：实际使用时，请替换为从浏览器中获取的真实cookies
        cookies = {
            'cf_clearance': 'dGbJdCifv94MB6CvL9APp3cpeGpIICHCqzmwKEQgs88-1719194070-1.0.1.1-p5UW2G4uexpNg9JI5Y3._mhEfvb8BkRUvIFjCrmZmEDPZjv6JSD3vaU9t6QYBv24j2ikoXN3iADRklZUdFOSqg ',  # 替换为实际的cf_clearance值
            # 其他必要的cookies，例如：
            # 'PHPSESSID': '你的PHPSESSID值',
            # 'uid': '你的uid值',
            # 'pass': '你的pass值'
        }
        
        # 从URL中提取域名，用于设置请求头
        host = parsed_url.netloc
        origin = f"https://{host}"
        referer = f"https://{host}/"
        
        # 设置请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
            "Referer": referer,
            "Origin": origin,
            "Host": host,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        logging.debug(f"开始请求URL: {url}")
        logging.debug(f"使用的请求头: {headers}")
        
        # 发送请求，带上cookies
        response = scraper.get(url, headers=headers, cookies=cookies)
        logging.debug(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logging.error(f"响应不是图片，而是: {content_type}")
                logging.error(f"响应内容: {response.text[:500]}")
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
            logging.error(f"错误响应内容: {response.text[:500]}")
            raise ValueError(f"下载失败，状态码: {response.status_code}")
            
    except Exception as e:
        logging.error(f"发生错误: {str(e)}")
        raise e

def save_cookies_to_file(cookies, filename="kamept_cookies.json"):
    """保存cookies到文件"""
    import json
    
    cookies_dir = Path("cookies")
    cookies_dir.mkdir(parents=True, exist_ok=True)
    
    cookies_path = cookies_dir / filename
    
    with open(cookies_path, 'w') as f:
        json.dump(cookies, f)
    
    print(f"Cookies已保存到: {cookies_path}")
    return cookies_path

def load_cookies_from_file(filename="kamept_cookies.json"):
    """从文件加载cookies"""
    import json
    
    cookies_path = Path("cookies") / filename
    
    if not cookies_path.exists():
        print(f"Cookies文件不存在: {cookies_path}")
        return None
    
    with open(cookies_path, 'r') as f:
        cookies = json.load(f)
    
    print(f"已从{cookies_path}加载cookies")
    return cookies

def test_download_with_saved_cookies():
    """使用保存的cookies下载需要通过Cloudflare保护的图片"""
    # 目标URL
    url = "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg.thumb.jpg"
    
    # 创建保存图片的目录
    save_dir = Path("downloads/kamept")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 从URL中提取文件名
    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    save_path = save_dir / f"saved_cookies_{file_name}"
    
    # 加载cookies
    cookies = load_cookies_from_file()
    if not cookies:
        print("未找到保存的cookies，请先运行test_download_with_selenium并手动完成验证")
        return False
    
    try:
        # 从URL中提取域名，用于设置请求头
        host = parsed_url.netloc
        origin = f"https://{host}"
        referer = f"https://{host}/"
        
        # 设置请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": referer,
            "Origin": origin,
            "Host": host,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        # 转换cookies格式
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        print(f"开始请求URL: {url}")
        print(f"使用的请求头: {headers}")
        
        # 发送请求，带上cookies
        response = requests.get(url, headers=headers, cookies=cookies_dict)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"响应不是图片，而是: {content_type}")
                print(f"响应内容: {response.text[:500]}")
                raise ValueError(f"响应不是图片: {content_type}")
            
            # 保存图片
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            # 验证文件
            file_size = os.path.getsize(save_path)
            print(f"保存的文件大小: {file_size} bytes")
            
            assert os.path.exists(save_path), "文件未创建"
            assert file_size > 0, "文件大小为0"
            print(f"图片已成功下载到: {save_path}")
            print(f"文件大小: {file_size} bytes")
            return True
        else:
            print(f"错误响应内容: {response.text[:500]}")
            raise ValueError(f"下载失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False

def test_download_with_selenium():
    """
    使用Selenium和undetected_chromedriver下载需要通过Cloudflare保护的图片
    
    注意：需要安装以下依赖：
    pip install selenium undetected-chromedriver
    
    并确保已安装Chrome浏览器
    """
    try:
        # 导入必要的库
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import base64
        
        # 目标URL
        url = "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg.thumb.jpg"
        
        # 创建保存图片的目录
        save_dir = Path("downloads/kamept")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 从URL中提取文件名
        parsed_url = urlparse(url)
        file_name = os.path.basename(parsed_url.path)
        save_path = save_dir / f"selenium_{file_name}"
        
        # 配置Chrome选项
        options = uc.ChromeOptions()
        # 禁用无头模式，显示浏览器窗口以便手动完成验证
        # options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # 创建一个undetected_chromedriver实例
        print("启动Chrome浏览器...")
        driver = uc.Chrome(options=options)
        
        try:
            # 先访问网站首页，通过Cloudflare验证
            home_url = "https://kamept.com/"
            print(f"访问网站首页: {home_url}")
            driver.get(home_url)
            
            # 等待用户手动完成验证（如果需要）
            print("请在浏览器中完成人机验证（如果出现），然后按Enter键继续...")
            input()
            
            # 等待页面加载完成（等待页面标题不包含"Just a moment"，这通常是Cloudflare验证页面的标题）
            try:
                WebDriverWait(driver, 10).until_not(
                    EC.title_contains("Just a moment")
                )
                print("Cloudflare验证已通过")
            except:
                print("等待超时，但可能已经通过验证")
            
            print("获取cookies...")
            cookies = driver.get_cookies()
            
            # 保存cookies到文件
            save_cookies_to_file(cookies)
            
            # 访问图片URL
            print(f"访问图片URL: {url}")
            driver.get(url)
            
            # 等待图片加载完成
            time.sleep(5)
            
            # 获取图片内容
            # 方法1：直接保存页面截图
            driver.save_screenshot(str(save_path.with_suffix('.png')))
            print(f"页面截图已保存到: {save_path.with_suffix('.png')}")
            
            # 方法2：尝试获取图片元素并下载
            try:
                # 找到图片元素
                img_element = driver.find_element(By.TAG_NAME, "img")
                
                # 获取图片的src属性
                img_src = img_element.get_attribute("src")
                
                if img_src.startswith("data:image"):
                    # 如果是base64编码的图片
                    img_data = img_src.split(",")[1]
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(img_data))
                else:
                    # 如果是URL，使用requests下载
                    # 从浏览器获取cookies
                    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                    
                    # 设置请求头
                    headers = {
                        "User-Agent": driver.execute_script("return navigator.userAgent"),
                        "Referer": home_url
                    }
                    
                    # 下载图片
                    img_response = requests.get(img_src, headers=headers, cookies=cookies_dict)
                    
                    if img_response.status_code == 200:
                        with open(save_path, "wb") as f:
                            f.write(img_response.content)
                        print(f"图片已成功下载到: {save_path}")
                    else:
                        print(f"下载图片失败，状态码: {img_response.status_code}")
            
            except Exception as e:
                print(f"获取图片元素失败: {str(e)}")
                
            # 验证文件是否存在
            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                print(f"文件大小: {file_size} bytes")
                return True
            else:
                print("文件未创建")
                return False
                
        finally:
            # 等待用户确认后关闭浏览器
            print("按Enter键关闭浏览器...")
            input()
            driver.quit()
            print("浏览器已关闭")
            
    except ImportError as e:
        print(f"缺少必要的库: {str(e)}")
        print("请安装所需依赖: pip install selenium undetected-chromedriver")
        return False
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False

def test_download_with_curl():
    """使用curl命令下载需要通过Cloudflare保护的图片"""
    # 目标URL
    url = "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg.thumb.jpg"
    
    # 创建保存图片的目录
    save_dir = Path("downloads/kamept")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 从URL中提取文件名
    file_name = os.path.basename(urlparse(url).path)
    save_path = save_dir / f"curl_{file_name}"
    
    try:
        # 使用os.system执行curl命令
        # 注意：需要替换以下cookie和user-agent为实际值
        cookie = "cf_clearance=你的cf_clearance值; 其他cookies..."  # 替换为实际的cookies
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        referer = "https://kamept.com/"
        
        # 构建curl命令
        curl_cmd = f'curl -s -o "{save_path}" -L "{url}" ' \
                  f'--cookie "{cookie}" ' \
                  f'--user-agent "{user_agent}" ' \
                  f'--referer "{referer}"'
        
        print(f"执行curl命令: {curl_cmd}")
        exit_code = os.system(curl_cmd)
        
        if exit_code == 0 and os.path.exists(save_path):
            file_size = os.path.getsize(save_path)
            if file_size > 0:
                print(f"图片已成功下载到: {save_path}")
                print(f"文件大小: {file_size} bytes")
                return True
            else:
                print("下载的文件大小为0")
                return False
        else:
            print(f"curl命令执行失败，退出码: {exit_code}")
            return False
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False

def test_download_with_stealth():
    """
    使用selenium-stealth库下载需要通过Cloudflare保护的图片
    
    注意：需要安装以下依赖：
    pip install selenium selenium-stealth undetected-chromedriver
    
    并确保已安装Chrome浏览器
    """
    try:
        # 导入必要的库
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import selenium_stealth
        import base64
        import time
        
        # 目标URL
        url = "https://kamept.com/attachments/202503/202503090238386e70e36905ff44a8e3dcaec602671760.jpg.thumb.jpg"
        
        # 创建保存图片的目录
        save_dir = Path("downloads/kamept")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 从URL中提取文件名
        parsed_url = urlparse(url)
        file_name = os.path.basename(parsed_url.path)
        save_path = save_dir / f"stealth_{file_name}"
        
        # 配置Chrome选项
        options = Options()
        # 禁用无头模式，显示浏览器窗口以便手动完成验证
        # options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 创建Chrome驱动
        print("启动Chrome浏览器...")
        driver = webdriver.Chrome(options=options)
        
        # 应用stealth设置
        selenium_stealth.stealth(
            driver,
            languages=["zh-CN", "zh", "en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        try:
            # 先访问网站首页，通过Cloudflare验证
            home_url = "https://kamept.com/"
            print(f"访问网站首页: {home_url}")
            driver.get(home_url)
            
            # 等待用户手动完成验证（如果需要）
            print("请在浏览器中完成人机验证（如果出现），然后按Enter键继续...")
            input()
            
            # 等待页面加载完成
            try:
                WebDriverWait(driver, 10).until_not(
                    EC.title_contains("Just a moment")
                )
                print("Cloudflare验证已通过")
            except:
                print("等待超时，但可能已经通过验证")
            
            print("获取cookies...")
            cookies = driver.get_cookies()
            
            # 保存cookies到文件
            save_cookies_to_file(cookies, "kamept_stealth_cookies.json")
            
            # 访问图片URL
            print(f"访问图片URL: {url}")
            driver.get(url)
            
            # 等待图片加载完成
            time.sleep(5)
            
            # 获取图片内容
            # 方法1：直接保存页面截图
            driver.save_screenshot(str(save_path.with_suffix('.png')))
            print(f"页面截图已保存到: {save_path.with_suffix('.png')}")
            
            # 方法2：尝试获取图片元素并下载
            try:
                # 找到图片元素
                img_element = driver.find_element(By.TAG_NAME, "img")
                
                # 获取图片的src属性
                img_src = img_element.get_attribute("src")
                
                if img_src.startswith("data:image"):
                    # 如果是base64编码的图片
                    img_data = img_src.split(",")[1]
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(img_data))
                else:
                    # 如果是URL，使用requests下载
                    # 从浏览器获取cookies
                    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                    
                    # 设置请求头
                    headers = {
                        "User-Agent": driver.execute_script("return navigator.userAgent"),
                        "Referer": home_url
                    }
                    
                    # 下载图片
                    img_response = requests.get(img_src, headers=headers, cookies=cookies_dict)
                    
                    if img_response.status_code == 200:
                        with open(save_path, "wb") as f:
                            f.write(img_response.content)
                        print(f"图片已成功下载到: {save_path}")
                    else:
                        print(f"下载图片失败，状态码: {img_response.status_code}")
            
            except Exception as e:
                print(f"获取图片元素失败: {str(e)}")
                
            # 验证文件是否存在
            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                print(f"文件大小: {file_size} bytes")
                return True
            else:
                print("文件未创建")
                return False
                
        finally:
            # 等待用户确认后关闭浏览器
            print("按Enter键关闭浏览器...")
            input()
            driver.quit()
            print("浏览器已关闭")
            
    except ImportError as e:
        print(f"缺少必要的库: {str(e)}")
        print("请安装所需依赖: pip install selenium selenium-stealth undetected-chromedriver")
        return False
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("尝试方法1：使用cloudscraper自动绕过Cloudflare")
    try:
        test_download_kamept_image()
    except Exception as e:
        print(f"方法1失败: {str(e)}")
        
        print("\n尝试方法2：使用预设cookies")
        print("注意：使用方法2前，请先在代码中设置正确的cookies值")
        # 注释掉方法2，因为需要实际的cookie值
        test_download_with_cookies()
        
        # print("\n尝试方法3：使用Selenium和undetected_chromedriver")
        # print("注意：需要安装selenium和undetected_chromedriver库")
        # success = test_download_with_selenium()
        
        # if success:
        #     print("\n尝试方法5：使用保存的cookies")
        #     test_download_with_saved_cookies()
        
        # print("\n尝试方法6：使用selenium-stealth")
        # print("注意：需要安装selenium-stealth库")
        # test_download_with_stealth()
        
        # print("\n尝试方法4：使用curl命令")
        # print("注意：使用方法4前，请先在代码中设置正确的cookies值")
        # test_download_with_curl()

import requests
import json
def main():
    """使用FlareSolverr绕过Cloudflare保护下载图片"""
    try:
        # FlareSolverr API请求
        flaresolverr_url = "https://fs.luckynex.cn:4310/v1"
        target_url = "https://www.google.com"
        
        # 设置代理
        proxy = {
            "url": "http://192.168.10.20:20171",  # 替换为你的代理地址
            # "username": "user",  # 可选,替换为你的代理用户名
            # "password": "pass"   # 可选,替换为你的代理密码
        }
        
        payload = {
            "cmd": "request.get",
            "url": target_url,
            "maxTimeout": 120000,
            "proxy": proxy
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        print(f"正在请求FlareSolverr API...")
        response = requests.post(flaresolverr_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"FlareSolverr响应状态: {result.get('status')}")
            
            if result.get('status') == 'ok':
                solution = result.get('solution', {})
                print(f"响应状态码: {solution.get('status')}")
                print(f"响应头: {solution.get('headers')}")
                
                # 获取cookies和User-Agent
                cookies = solution.get('cookies', [])
                user_agent = solution.get('userAgent')
                print(f"获取到的Cookies: {cookies}")
                print(f"获取到的User-Agent: {user_agent}")
                
                # 检查响应内容类型
                content_type = solution.get('headers', {}).get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"响应不是图片，而是: {content_type}")
                    return False
                
                return True
            else:
                print(f"FlareSolverr请求失败: {result.get('message')}")
                return False
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False


if __name__ == "__main__":
    main()

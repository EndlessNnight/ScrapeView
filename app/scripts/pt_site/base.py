from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .schemas import TorrentInfo, TorrentDetails, SiteConfig, Category, TorrentInfoList, ApiSiteConfig

class BaseSiteParser(ABC):
    """站点解析器基类"""
    
    @abstractmethod
    def parse_torrent_list(self, soup: BeautifulSoup) -> TorrentInfoList:
        """解析种子列表页面"""
        pass
    
    @abstractmethod
    def parse_torrent_detail(self, soup: BeautifulSoup) -> TorrentDetails:
        """解析种子详情页面"""
        pass
    
    @abstractmethod
    def parse_user_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """解析用户信息页面"""
        pass

class BasePTSite(ABC):
    """PT站点基类"""
    
    def __init__(self, site_config: SiteConfig, parser: BaseSiteParser):
        self.config = site_config
        self.base_url = site_config.base_url.rstrip('/')
        self.session = requests.Session()
        self.parser = parser
    
    def set_headers(self, headers: Dict[str, str]) -> None:
        """设置请求头"""
        self.session.headers.update(headers)
        
    def set_cookies(self, cookies: Dict[str, str] | str) -> None:
        """设置cookies
        
        Args:
            cookies: cookie字典或cookie字符串
        """
        if isinstance(cookies, str):
            cookie_pairs = cookies.split(';')
            for pair in cookie_pairs:
                pair = pair.strip()
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    self.session.cookies.set(key.strip(), value.strip())
        else:
            for key, value in cookies.items():
                self.session.cookies.set(key, value)
            
    def set_proxy(self, proxy: str) -> None:
        """设置代理"""
        self.session.proxies.update({"http": proxy, "https": proxy}) 

    def _get_page(self, url: str, params: Optional[Dict[str, Any]] = None, parser: str = 'html.parser') -> BeautifulSoup:
        """获取页面内容"""
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"请求失败: {response.status_code}")
        # with open(f'{self.config.site_name}.html', 'w', encoding='utf-8') as f:
        #     f.write(response.text)
        return BeautifulSoup(response.text, parser)
    
    
    def get_all_category(self) -> List[Category]:
        """获取所有分类"""
        if self.category_mapping:
            return [Category(id=cat_id, name=self.category_mapping[cat_id].name) for cat_id in self.category_mapping]
        else:
            return []

    @abstractmethod
    def get_torrents(self, **kwargs) -> TorrentInfoList:
        """获取种子列表"""
        pass
    
    @abstractmethod
    def get_details(self, torrent_id: int) -> TorrentDetails:
        """获取种子详情"""
        pass
    
    @abstractmethod
    def get_search(self, keyword: str) -> TorrentInfoList:
        """搜索种子"""
        pass
    
    @abstractmethod
    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        pass
    
    @abstractmethod
    def get_torrent_files(self, torrent_id: int) -> bytes:
        """获取种子文件列表"""
        pass

class BaseApiSite(ABC):
    """API站点基类"""
    def __init__(self, site_config: ApiSiteConfig):
        self.config = site_config
        self.base_url = site_config.base_url.rstrip('/')
        self.session = requests.Session()
        self.api_key = None

    def get_all_category(self) -> List[Category]:
        """获取所有分类"""
        if self.category_mapping:
            return [Category(id=cat_id, name=self.category_mapping[cat_id].name) for cat_id in self.category_mapping]
        else:
            return []

    def set_headers(self, headers: Dict[str, str]) -> None:
        """设置请求头"""
        self.session.headers.update(headers)
    
    def set_api_key(self, api_key: str) -> None:
        """设置API密钥"""
        self.api_key = api_key

    def set_auth_token(self, auth_token: str) -> None:
        """设置认证令牌"""
        self.session.headers['Authorization'] = f'Bearer {auth_token}'

    def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取JSON数据"""
        if self.api_key:
            params['apikey'] = self.api_key
        else:
            raise Exception("API密钥未设置")
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"请求失败: {response.status_code}")
        return response.json()
    
    def _post_json(self, url: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送POST请求获取JSON数据"""
        if self.api_key:
            data['apikey'] = self.api_key
        else:
            raise Exception("API密钥未设置")
        response = self.session.post(url, json=data)
        if response.status_code != 200:
            raise Exception(f"请求失败: {response.status_code}")
        return response.json()

    @abstractmethod
    def get_torrents(self, **kwargs) -> List[TorrentInfo]:
        """获取种子列表"""
        pass

    @abstractmethod
    def get_details(self, torrent_id: int) -> TorrentDetails:
        """获取种子详情"""
        pass

    @abstractmethod
    def get_search(self, keyword: str) -> List[TorrentInfo]:
        """搜索种子"""
        pass

    @abstractmethod
    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        pass
    
    @abstractmethod
    def get_torrent_files(self, torrent_id: int) -> bytes:
        """获取种子文件列表"""
        pass

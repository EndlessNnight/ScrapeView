import json
from datetime import datetime
from pydantic import HttpUrl
from typing import Dict, Any, List, Tuple
from ..base import BasePTSite
from ..schemas import TorrentInfo, TorrentDetails, SiteConfig, PTUserInfo, CategoryDetail, TorrentInfoList
from ..parser.hhanclub import HHAnClubParser
from bs4 import BeautifulSoup



class DateTimeEncoder(json.JSONEncoder):
    """处理datetime的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class HHAnClubSite(BasePTSite):
    """HDFans站点实现"""
    
    def __init__(self):
        config = SiteConfig(
            site_name="HHAnClub",
            base_url="https://hhanclub.top",
            login_url="/takelogin.php",
            torrents_url="/torrents.php",
            details_url="/details.php",
            search_url="/torrents.php",
            user_info_url="/index.php",
            # default_categories=[401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413]
        )

        self.category_mapping = {
            401: CategoryDetail(id=401, name="电影", params="cat[]=401"),
            402: CategoryDetail(id=402, name="电视剧", params="cat[]=402"),
            403: CategoryDetail(id=403, name="综艺", params="cat[]=403"),
            405: CategoryDetail(id=405, name="动漫", params="cat[]=405"),
            404: CategoryDetail(id=404, name="纪录片", params="cat[]=404"),
            407: CategoryDetail(id=407, name="体育", params="cat[]=407"),
        }

        super().__init__(config, HHAnClubParser())
    
    def _is_login_page(self, soup) -> bool:
        """检查页面是否是登录页面
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            bool: 如果是登录页面则返回True，否则返回False
        """
        # 检查是否包含登录表单
        login_form = soup.find('form', {'action': 'takelogin.php'})
        if login_form:
            return True
            
        # 检查页面标题是否包含"登录"字样
        title = soup.find('title')
        if title and '登录' in title.text:
            return True
            
        # 检查是否有登录按钮
        login_button = soup.find('input', {'type': 'submit', 'value': '登录'})
        if login_button:
            return True
            
        return False
    
    def is_logged_in(self) -> bool:
        """检查用户是否已登录
        
        Returns:
            bool: 如果用户已登录则返回True，否则返回False
        """
        # 首先检查是否设置了cookie
        if not self.session.cookies:
            return False
            
        # 访问首页检查是否已登录
        try:
            soup = self._get_page(f"{self.base_url}/index.php")
            
            # 检查是否是登录页面
            if self._is_login_page(soup):
                return False
                
            # 检查是否有用户信息元素，表示已登录
            # 这里需要根据实际网站结构调整选择器
            user_info_element = soup.select_one('a[href*="usercp.php"]')
            return user_info_element is not None
        except Exception as e:
            print(f"检查登录状态时出错: {e}")
            return False
        

    def get_torrents(self, **kwargs) -> TorrentInfoList:
        """获取种子列表
        
        Args:
            **kwargs: 查询参数
                page: 页码
                cat_ids: 分类ID列表
        """
        params = {
            "inclbookmarked": 0,
            "incldead": 1,
            "spstate": 0,
            "page": kwargs.get('page', 0),
        }
        
        # 添加分类参数
        cat_id = kwargs.get('cat_id', None)
        if cat_id and cat_id in self.category_mapping:
            add_params = self.category_mapping[cat_id].params.split("&")
            for param in add_params:
                key, value = param.split("=")
                params[key] = value
        soup = self._get_page(f"{self.base_url}{self.config.torrents_url}", params)
        return self.parser.parse_torrent_list(soup)

    def get_details(self, torrent_id: int) -> TorrentDetails:
        """获取种子详情
        
        Args:
            torrent_id: 种子ID
        """
        soup = self._get_page(f"{self.base_url}{self.config.details_url}?id={torrent_id}")
        return self.parser.parse_torrent_detail(soup)
    
    def get_search(self, keyword: str) -> TorrentInfoList:
        """搜索种子
        
        Args:
            keyword: 搜索关键词
        """
        params = {
            "search": keyword,
            "search-mode": 0,
            "incldead": 1,
            "spstate": 0,
            "inclbookmarked": 0,
            "search_area": 0,
            "search_all": 1
        }

        soup = self._get_page(f"{self.base_url}{self.config.search_url}", params)
        return self.parser.parse_torrent_list(soup)

    def get_user_info(self) -> PTUserInfo:
        """获取用户信息"""
        soup = self._get_page(f"{self.base_url}{self.config.user_info_url}")
        return self.parser.parse_user_info(soup)

    def get_download_url(self, torrent_id: int) -> str:
        """获取种子下载链接
        
        Args:
            torrent_id: 种子ID
        """
        return f"{self.base_url}/download.php?id={torrent_id}"

    def get_torrent_files(self, torrent_id: int):
        """获取种子文件列表
        
        Args:
            torrent_id: 种子ID
            
        Returns:
            bytes: 种子文件的二进制数据
        """
        # 构建下载链接
        download_url = f"{self.base_url}/download.php?id={torrent_id}"
        
        # 发送请求获取种子文件
        response = self.session.get(download_url)
        
        # 检查响应状态
        if response.status_code != 200:
            raise Exception(f"下载种子文件失败: HTTP {response.status_code}")
            
        # 直接返回二进制数据，不保存到本地文件
        return response.content


def main():
    """主函数"""
    hhanclub = HHAnClubSite()
    hhanclub.set_cookies("c_secure_uid=MTI1MzM%3D; c_secure_pass=ad57665d93fa13e7b099ed3ebd42b109; c_secure_ssl=eWVhaA%3D%3D; c_secure_tracker_ssl=eWVhaA%3D%3D; c_secure_login=bm9wZQ%3D%3D; cf_clearance=fJ18OSLYDRbqdFANerXGMhqoCJ2IQFowwFUZK27JeFI-1731464067-1.2.1.1-Y69g_ugEoC9Y4dO.Mx2O.Pe2zLXUHMY09gHx4KT6A5jPnlNBSb5_i2stOqI7mLZeNk8IKx4geBSs1CyJorgvXgjlkrSmLv3.yfJoAaeYHCqWWvxgMMQcXG8HXmgeL5r2EhdopjiKHy0O_S57hAqfJQFBn8IBbRFEYm367fWfZmXp9K6bre.jy1fLt9jcGyDYEdTp8mPoMvo2sP0s7gEDkClJ2fWg4zmQMowSu03aOBiVFdRnIgLncChtsSo2DbMIJDPmoJcKVzctRTP1pOFvkA_7rQ9tUAr9ftZY9uRc34VoCC1dxGQBraLfLsCkFpPFZDORv0KyAYHfd6jbWEW3mUbhnUKSKiU.rt8B2RXR6EURykD9xVhKpG.Gj6yd2sLm1r7VDMLqDqc_6wZyjWnZZLZkP4.giCU1t5tDK8_1398H6cfVxFZTvWn4lyt3uDh5")
    # print(hhanclub.get_search("九州千秋令"))
    print(hhanclub.get_details(155326))


if __name__ == "__main__":
    main()

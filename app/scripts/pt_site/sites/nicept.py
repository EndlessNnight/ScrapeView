import json
from datetime import datetime
from pydantic import HttpUrl
from typing import Dict, Any, List
from ..base import BasePTSite
from ..schemas import TorrentInfo, TorrentDetails, SiteConfig, PTUserInfo, CategoryDetail
from ..parser.nexusphp import NexusphpParser



class DateTimeEncoder(json.JSONEncoder):
    """处理datetime的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class NicePT(BasePTSite):
    """NicePT站点实现"""
    
    def __init__(self):
        config = SiteConfig(
            site_name="NicePT",
            base_url="https://www.nicept.net",
            login_url="/takelogin.php",
            torrents_url="/torrents.php",
            details_url="/details.php",
            search_url="/torrents.php",
            user_info_url="/index.php",
            # default_categories=[401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413]
        )
        self.category_mapping = {}
        super().__init__(config, NexusphpParser())  
    
    
    def get_torrents(self, **kwargs) -> List[TorrentInfo]:
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
        cat_ids = kwargs.get('cat_ids', self.config.default_categories)
        for cat_id in cat_ids:
            params[f"cat{cat_id}"] = 1
        print(f"{self.base_url}{self.config.torrents_url}")
        print(params)
        soup = self._get_page(f"{self.base_url}{self.config.torrents_url}", params)
        return self.parser.parse_torrent_list(soup)

    def get_details(self, torrent_id: int) -> TorrentDetails:
        """获取种子详情
        
        Args:
            torrent_id: 种子ID
        """
        soup = self._get_page(f"{self.base_url}{self.config.details_url}?id={torrent_id}")
        return self.parser.parse_torrent_detail(soup)
    
    def get_search(self, keyword: str) -> List[TorrentInfo]:
        """搜索种子
        
        Args:
            keyword: 搜索关键词
        """
        soup = self._get_page(f"{self.base_url}{self.config.search_url}?search={keyword}")
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
    pass



if __name__ == "__main__":
    main()

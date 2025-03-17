import json
from datetime import datetime
from pydantic import HttpUrl
from typing import Dict, Any, List
from ..base import BasePTSite
from ..schemas import TorrentInfo, TorrentDetails, SiteConfig, PTUserInfo, CategoryDetail, TorrentInfoList
from ..parser.nexusphp import NexusphpParser



class DateTimeEncoder(json.JSONEncoder):
    """处理datetime的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class KameptSite(BasePTSite):
    """Kamept站点实现"""
    
    def __init__(self):
        config = SiteConfig(
            site_name="Kamept",
            base_url="https://kamept.com",
            login_url="/takelogin.php",
            torrents_url="/torrents.php",
            details_url="/details.php",
            search_url="/torrents.php",
            user_info_url="/index.php",
        )

        self.category_mapping = {
            # 1: CategoryDetail(id=1, name="官方", params="tag=gf"),
        }

        super().__init__(config, NexusphpParser())
    

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
        if cat_id in self.category_mapping:
            params_str = self.category_mapping[cat_id].params.split("&")
            for param in params_str:
                    key, value = param.split("=")
                    params[key] = value
        soup = self._get_page(f"{self.base_url}{self.config.torrents_url}", params)
        data_list = self.parser.parse_torrent_list(soup)
        for data in data_list.torrents:
            if not data.cover_url.startswith(('http://', 'https://')):
                data.cover_url = f"{self.base_url}/{data.cover_url.lstrip('/')}"
        return data_list

    def get_details(self, torrent_id: int) -> TorrentDetails:
        """获取种子详情
        
        Args:
            torrent_id: 种子ID
        """
        soup = self._get_page(f"{self.base_url}{self.config.details_url}?id={torrent_id}")
        details = self.parser.parse_torrent_detail(soup)
        for i, descr_image in enumerate(details.descr_images):
            if not descr_image.startswith(('http://', 'https://')):
                details.descr_images[i] = f"{self.base_url}/{descr_image.lstrip('/')}"
        return details
    
    def get_search(self, keyword: str) -> TorrentInfoList:
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
    kamept = KameptSite()
    print(kamept.get_all_category())



if __name__ == "__main__":
    main()

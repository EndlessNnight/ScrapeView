from ..base import BasePTSite
from ..schemas import TorrentInfo, TorrentDetails, SiteConfig, PTUserInfo, CategoryDetail, TorrentInfoList
from ..parser.nexusphp import NexusphpParser


class CsptSite(BasePTSite):
    """CSpt站点实现"""
    
    def __init__(self):
        config = SiteConfig(
            site_name="CSpt",
            base_url="https://cspt.top",
            login_url="/takelogin.php",
            torrents_url="/torrents.php",
            details_url="/details.php",
            search_url="/torrents.php",
            user_info_url="/index.php",
            # default_categories=[401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413]
        )

        self.category_mapping = {
            3: CategoryDetail(id=3, name="官种", params="tag_id=3"),
            401: CategoryDetail(id=401, name="电影", params="cat=401"),
            402: CategoryDetail(id=402, name="电视剧", params="cat=402"),
            403: CategoryDetail(id=403, name="综艺", params="cat=403"),
            404: CategoryDetail(id=404, name="纪录片", params="cat=404"),
            405: CategoryDetail(id=405, name="动漫", params="cat=405"),
            408: CategoryDetail(id=408, name="音乐", params="cat=408"),
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
        url = f"{self.base_url}{self.config.torrents_url}"
        if cat_id and cat_id in self.category_mapping:
            if self.category_mapping[cat_id].params:
                params_list = self.category_mapping[cat_id].params.split("&")
                for param in params_list:
                    add_params = param.split("=")
                    params[add_params[0]] = add_params[1]
            if self.category_mapping[cat_id].url:
                url = f"{self.base_url}{self.category_mapping[cat_id].url}"

        soup = self._get_page(url, params)
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

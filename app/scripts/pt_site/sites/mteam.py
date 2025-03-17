from ..base import BaseApiSite
from ..schemas import TorrentInfo, TorrentDetails, SiteConfig, PTUserInfo, CategoryDetail, TorrentInfoList, ApiSiteConfig
from .schemas.mteam.search import RequestModel, ResponseModel, RequestSearch
from .schemas.mteam.detail import ResponseModel as DetailResponseModel
from .schemas.mteam.profile import ResponseModel as UserInfoResponseModel
from .schemas.mteam.myPeerStatus import ResponseModel as UserInfoPeerResponseModel
from .schemas.mteam.torrentGenDlToken import TorrentGenDlTokenResponse, TorrentGenDlTokenRequest

from typing import Dict, Any, List, Optional

class MTeamSite(BaseApiSite):
    def __init__(self):
        config = ApiSiteConfig(
            site_name="M-Team",
            base_url="https://api.m-team.io",
            torrents_url="/api/torrent/search",
            details_url="/api/torrent/detail",
            search_url="/api/torrent/search",
            user_info_url="/api/member/profile",
            user_info_peer_url="/api/tracker/myPeerStatus",
            torrent_files_url="/api/torrent/genDlToken"
        )
        self.discount_table = {
            "PERCENT_50": "50%",
            "PERCENT_30": "30%",
            "PERCENT_10": "10%",
            "PERCENT_5": "5%",
            "PERCENT_1": "1%",
            "FREE": "免费",
        }
        self.category_mapping = {
            1: CategoryDetail(id=1, name="电影", params="movie"),
            2: CategoryDetail(id=2, name="电视剧", params="tvshow"),
            3: CategoryDetail(id=3, name="成人", params="adult"),
        }
        super().__init__(config)
        self._init_user_agent()

    def _init_user_agent(self):
        """初始化用户代理"""
        self.session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"

    def _is_login(self):
        """判断是否登录"""
        if self.session.headers.get("x-api-key") and self.session.headers.get("Authorization"):
            return True
        return False
    
    def set_api_key(self, api_key: str) -> None:
        """设置API密钥"""
        self.api_key = api_key
        self.session.headers["x-api-key"] = self.api_key
    
    def get_torrents(self, categories: List[str] = [], page: int = 1, page_size: int = 100, mode: str = "normal", visible: int = 1, keyword: str = None, cat_id: int = None)->TorrentInfoList:
        """获取种子列表
        
        Args:
            categories: 分类列表
            page: 页码，从1开始
            page_size: 每页数量
            mode: 搜索模式，默认为movie
            visible: 可见性，0全部，1可见，2不可见
            keyword: 搜索关键词
        
        Returns:
            ResponseModel: 响应模型
        """
        if not self._is_login():
            raise Exception("未登录")
        url = f"{self.base_url}{self.config.torrents_url}"
        if cat_id and cat_id in self.category_mapping:
            if self.category_mapping[cat_id].params:
                mode = self.category_mapping[cat_id].params
                
            if self.category_mapping[cat_id].url:
                url = f"{self.base_url}{self.category_mapping[cat_id].url}"

        # 构建请求参数
        request_data = RequestSearch(
            categories=categories,
            mode=mode,
            pageNumber=page,
            pageSize=page_size,
            visible=visible
        )
       
        # 如果提供了关键词，添加到请求参数中
        if keyword:
            request_data.keyword = keyword

        data = request_data.model_dump()
        response = self._post_json_with_header(url, data)
        data = ResponseModel(**response)
        if data.code != '0' or data.message != 'SUCCESS':
            raise Exception(f"请求失败: {data.message}")
        torrents = []
        for item in data.data.data:
            tags = []
            if item.tags:
                tags = item.tags.split("、")
                
            # 转换字节大小为合适的单位
            size_bytes = float(item.size)
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            size_unit = 0
            while size_bytes >= 1024 and size_unit < len(units)-1:
                size_bytes /= 1024
                size_unit += 1
            size_str = f"{size_bytes:.2f}{units[size_unit]}"
            
            torrents.append(TorrentInfo(
                torrent_id=item.id,
                title=item.name,
                subtitle=item.small_descr,
                cover_url=item.image_list[0] if item.image_list else None,
                tags=tags,
                discount=item.status.discount,
                free_until=item.status.discount_end_time,
                size=size_str,
                seeders=item.status.seeders,
                leechers=item.status.leechers,
                up_time=item.created_date
            ))
        return TorrentInfoList(torrents=torrents)
    def _post_json_with_header(self, url: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送POST请求获取JSON数据，使用请求头中的API密钥"""
        response = self.session.post(url, json=data)
        if response.status_code != 200:
            raise Exception(f"请求失败: {response.status_code}")
        return response.json()
    
    def _post_params_with_header(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送POST请求获取JSON数据，使用请求头中的API密钥"""
        response = self.session.post(url, params=params)
        if response.status_code != 200:
            raise Exception(f"请求失败: {response.status_code}")
        return response.json()

    def get_details(self, torrent_id: int) -> TorrentDetails:
        """获取种子详情"""
        if not self._is_login():
            raise Exception("未登录")
        
        response = self._post_params_with_header(f"{self.base_url}{self.config.details_url}", {"id": torrent_id})
        data = DetailResponseModel(**response)
        if data.code != '0' or data.message != 'SUCCESS':
            raise Exception(f"请求失败: {data.message}")
        return TorrentDetails(
            title=data.data.name,
            subtitle=data.data.small_descr,
            descr_images=data.data.image_list,
            peers_info=f"{data.data.status.seeders}个做种者 | {data.data.status.leechers}个下载者",
            info_text=f"体积：{float(data.data.size)/(1024**3):.2f}GB 折扣：{self.discount_table[data.data.status.discount] or data.data.status.discount} 免费至：{data.data.status.discount_end_time}"
        )

    def get_search(self, keyword: str) -> TorrentInfoList:
        """搜索种子
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            ResponseModel: 响应模型
        """
        return self.get_torrents(keyword=keyword)

    def get_user_info(self):
        """获取用户信息"""
        if not self._is_login():
            raise Exception("未登录")
        
        response = self._post_params_with_header(f"{self.base_url}{self.config.user_info_url}")
        data = UserInfoResponseModel(**response)
        if data.code != '0' or data.message != 'SUCCESS':
            raise Exception(f"请求失败: {data.message}")


        # 将字节数转换为GB或TB字符串
        downloaded_bytes = int(data.data.member_count.downloaded)
        if downloaded_bytes >= 1024 * 1024 * 1024 * 1024:  # TB
            downloaded_str = f"{downloaded_bytes / (1024 * 1024 * 1024 * 1024):.2f} TB"
        elif downloaded_bytes >= 1024 * 1024 * 1024:  # GB
            downloaded_str = f"{downloaded_bytes / (1024 * 1024 * 1024):.2f} GB"
        else:  # MB
            downloaded_str = f"{downloaded_bytes / (1024 * 1024):.2f} MB"
        uploaded_bytes = int(data.data.member_count.uploaded)
        if uploaded_bytes >= 1024 * 1024 * 1024 * 1024:  # TB
            uploaded_str = f"{uploaded_bytes / (1024 * 1024 * 1024 * 1024):.2f} TB"
        elif uploaded_bytes >= 1024 * 1024 * 1024:  # GB
            uploaded_str = f"{uploaded_bytes / (1024 * 1024 * 1024):.2f} GB"
        else:  # MB
            uploaded_str = f"{uploaded_bytes / (1024 * 1024):.2f} MB"

        response = self._post_params_with_header(f"{self.base_url}{self.config.user_info_peer_url}")
        user_peer_data = UserInfoPeerResponseModel(**response)
        if user_peer_data.code != '0' or user_peer_data.message != 'SUCCESS':
            raise Exception(f"请求失败: {user_peer_data.message}")

        return PTUserInfo(
            username=data.data.username,
            bonus=data.data.member_count.bonus,
            ratio=data.data.member_count.share_rate,
            uploaded=uploaded_str,
            downloaded=downloaded_str,
            seeding=user_peer_data.data.seeder,
            leeching=user_peer_data.data.leecher
        )
    def get_torrent_files(self, torrent_id: int) -> bytes:
        """获取种子文件"""
        if not self._is_login():
            raise Exception("未登录")
        request_data = TorrentGenDlTokenRequest(id=torrent_id)
        response = self._post_params_with_header(f"{self.base_url}{self.config.torrent_files_url}", request_data.model_dump())
        data = TorrentGenDlTokenResponse(**response)
        if data.code != '0' or data.message != 'SUCCESS':
            raise Exception(f"请求失败: {data.message}")
        # 发送请求获取种子文件
        response = self.session.get(data.data)
        return response.content

def main():
    mteam = MTeamSite()
    print(mteam.get_all_category())

if __name__ == "__main__":
    main()

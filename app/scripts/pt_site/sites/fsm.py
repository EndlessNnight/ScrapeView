from ..base import BaseApiSite
from ..schemas import TorrentInfo, TorrentDetails, PTUserInfo, CategoryDetail, TorrentInfoList, TorrentStatus, ApiSiteConfig
from .schemas.fsm.listTorrents import ResponseModel as ListTorrentsResponseModel, RequestModel as ListTorrentsRequestModel
from .schemas.fsm.userInfos import ResponseModel as UserInfoResponseModel
from .schemas.fsm.torrentsDetails import ResponseModel as TorrentDetailsResponseModel, RequestModel as TorrentDetailsRequestModel
import re
import time
from typing import Dict, Any, List, Optional


class FsmSite(BaseApiSite):
    def __init__(self):
        config = ApiSiteConfig(
            site_name="Fsm",
            base_url="https://fsm.name/",
            torrents_url="/api/Torrents/listTorrents",
            details_url="/api/Torrents/details",
            user_info_url="/api/Users/infos",
            torrent_files_url="https://api.fsm.name/Torrents/download",
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
            1: CategoryDetail(id=1, name="日本AV"),
            2: CategoryDetail(id=2, name="国产视频"),
            3: CategoryDetail(id=3, name="写真"),
            4: CategoryDetail(id=4, name="黄油"),
            5: CategoryDetail(id=5, name="里番"),
            6: CategoryDetail(id=6, name="黄色漫画"),
            7: CategoryDetail(id=7, name="欧美视频"),
            8: CategoryDetail(id=8, name="其他"),
            
        }
        super().__init__(config)
        self._init_user_agent()

    def _init_user_agent(self):
        """初始化用户代理"""
        self.session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"

    def _is_login(self):
        """判断是否登录"""
        if self.session.headers.get("APITOKEN"):
            return True
        return False
    
    def set_api_key(self, api_key: str) -> None:
        """设置API密钥"""
        self.api_key = api_key
        self.session.headers["APITOKEN"] = self.api_key

    def set_passkey(self, passkey: str) -> None:
        """设置passkey"""
        self.passkey = passkey

    def set_proxy(self, proxy: str) -> None:
        """设置代理"""
        self.session.proxies.update({"http": proxy, "https": proxy})

    
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

    def _get_with_header(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送GET请求获取JSON数据，使用请求头中的API密钥"""
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"请求失败: {response.status_code}")
        return response.json()
    
    def _extract_images_from_content(self, content: str) -> List[str]:
        """从内容中提取图片链接
        
        Args:
            content: 包含图片链接的内容字符串
            
        Returns:
            List[str]: 提取出的图片链接列表
        """        
        # 匹配图片链接的正则表达式
        pattern = r'https?://\S+?\.(?:jpg|jpeg|png|gif|webp)(?:\"|\s|\'|\\"|$)'
        
        # 查找所有匹配项
        matches = re.findall(pattern, content)
        
        # 清理匹配结果，移除末尾的引号或其他非URL字符
        cleaned_urls = []
        for url in matches:
            # 移除末尾的引号或其他非URL字符
            if url.endswith('"') or url.endswith("'") or url.endswith('\\\"'):
                url = url[:-1]
            cleaned_urls.append(url)
            
        return cleaned_urls

    def _timestamp_to_str(self, timestamp: int) -> str:
        """将时间戳转换为字符串"""
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

    def get_details(self, torrent_id: int) -> TorrentDetails:
        """获取种子详情"""
        if not self._is_login():
            raise Exception("未登录")
        
        request_data = TorrentDetailsRequestModel(
            tid=torrent_id,
            page=1
        )
        data = self._get_with_header(f"{self.base_url}{self.config.details_url}", request_data.model_dump())
        data = TorrentDetailsResponseModel(**data)
        if data.success != True:
            raise Exception(f"请求失败: {data.message}")
        torrent = data.data.torrent
        info_text = f"体积：{torrent.file_size}"
        discount_name = None
        free_until = None
        if torrent.status and torrent.status.name and torrent.status.end_at:
                discount_name = self.discount_table.get(torrent.status.name) or torrent.status.name
                free_until = self._timestamp_to_str(torrent.status.end_at)
                info_text += f" 折扣：{discount_name} 免费至：{free_until}"
        
        upload = 0
        download = 0
        if torrent.peers:
            upload = int(torrent.peers.upload)
            download = int(torrent.peers.download)
        return TorrentDetails(
            title=torrent.title,
            subtitle="",
            descr_images=self._extract_images_from_content(torrent.content),
            peers_info=f"{upload}个做种者 | {download}个下载者",
            info_text = info_text,
            seeders=upload,
            leechers=download,
            discount=discount_name,
            free_until=free_until
        )

    def get_torrents(self, **kwargs)->TorrentInfoList:
        """获取种子列表
        
        Args:
            page: 页码，从1开始
            keyword: 搜索关键词
        Returns:
            ResponseModel: 响应模型
        """
        
        
        if not self._is_login():
            print("未登录")
            raise Exception("未登录")

        page = kwargs.get('page', 1)
        cat_id = kwargs.get('cat_id', None)
        keyword = kwargs.get('keyword', None)
        if cat_id and cat_id in self.category_mapping:
            type = self.category_mapping[cat_id].id
        else:
            type = 0

        # 构建请求参数
        request_data = ListTorrentsRequestModel(
            page=page,
            type=type,
            systematics=0,
            tags=[],
            keyword=keyword
        )
       
        # 如果提供了关键词，添加到请求参数中
        if keyword:
            request_data.keyword = keyword

        data = request_data.model_dump()
        response = self._get_with_header(f"{self.base_url}{self.config.torrents_url}", data)
        data = ListTorrentsResponseModel(**response)
        if data.success != True:
            print(data.msg)
            raise Exception(f"请求失败: {data.msg}")
        torrents = []
        

        for item in data.data.list:
            download_status = TorrentStatus.NOT_DOWNLOAD
            download_progress = 0
            if item.snatchInfo:
                if item.snatchInfo.status == "SEED":
                    download_status = TorrentStatus.SEEDING
                elif item.snatchInfo.status == "STOP":
                    download_status = TorrentStatus.INACTIVITY
                download_progress = item.snatchInfo.progress or 0                
            torrents.append(TorrentInfo(
                torrent_id=item.tid,
                title=item.title,
                subtitle=None,
                cover_url=item.cover,
                tags=item.tags,
                discount=item.status.name,
                free_until=self._timestamp_to_str(item.status.endAt),
                size=item.fileSize,
                seeders=item.peers.upload,
                leechers=item.peers.download,
                up_time=self._timestamp_to_str(item.createdTs),
                finished=item.finish,
                download_status=download_status,
                download_progress=download_progress
            ))
        return TorrentInfoList(torrents=torrents)

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
        
        response = self._get_with_header(f"{self.base_url}{self.config.user_info_url}")
        data = UserInfoResponseModel(**response)
        if data.success != True:
            raise Exception(f"请求失败: {data.msg}")
        
        uploaded_str = ""
        downloaded_str = ""

        uploaded_str = self._convert_size(data.data.upload)
        downloaded_str = self._convert_size(data.data.download)
        
        return PTUserInfo(
            username=data.data.username,
            bonus=data.data.point,
            ratio=data.data.seed_gh,
            uploaded=uploaded_str,
            downloaded=downloaded_str,
            seeding=data.data.peers.upload,
            leeching=data.data.peers.download
        )
        
    def get_torrent_files(self, torrent_id: int) -> bytes:
        """获取种子文件列表"""
        if not self.passkey:    
            raise Exception("未设置passkey")
        response = self.session.get(f"{self.config.torrent_files_url}?tid={torrent_id}&passkey={self.passkey}&source=direct")
        # 检查响应状态
        if response.status_code != 200:
            raise Exception(f"下载种子文件失败: HTTP {response.status_code}")
            
        return response.content
        
    @staticmethod
    def _convert_size(size_bytes):
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.2f} {units[unit_index]}"

def main():
    fsm = FsmSite()

if __name__ == "__main__":
    main()

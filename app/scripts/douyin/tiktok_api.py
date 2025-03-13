from app.scripts.douyin import schemas
from app.scripts.douyin.abogus import ABogus
from app.scripts.douyin.data_schemas import Creator, following, hot_list, video_info, fetch_one_video, me_following
from app.scripts.douyin.urls import Urls
from app.services.douyin import get_douyin_cookie
from app.db.session import get_db
from fastapi import Depends

from urllib.parse import quote
import requests
import re


douyin_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
    # 'accept-encoding': None,
    # 'Cookie': constant.COOKIE,
}


class TikTokApi:

    def __init__(self, cookie: str = None):
        self.urls = Urls()
        self.headers = douyin_headers.copy()
        
        if cookie:
            self.headers["Cookie"] = cookie
        # self.logger = Logger("TiktokApi").get_logger()

    def get_user_info(self, sec_user_id) -> Creator.Base | None:
        params = schemas.Profile(sec_user_id=sec_user_id)
        params_dict = params.model_dump()
        params_dict["a_bogus"] = self.get_abogus(params_dict)
        url = self.urls.USER_DETAIL + self.dict_to_url_params(params_dict)
        res = requests.get(url=url, headers=self.headers)  # 使用实例的headers而不是全局headers
        if res.status_code == 200 and res.text != "":
            return Creator.Base(**res.json())
        return None
    
    def get_user_short_info(self):
        params = schemas.UserShortInfo()
        params_dict = params.model_dump()
        params_dict["a_bogus"] = self.get_abogus(params_dict)
        url = self.urls.USER_SHORT_INFO + self.dict_to_url_params(params_dict)
        res = requests.get(url=url, headers=self.headers)
        print(res.json())
        # return UserShortInfo.Base(**res.json())


    def get_me_following_list(self, count: int = 50, max_time: int = 0, min_time: int = 0) -> me_following.Base | None:
        params = schemas.FollowingList(count=count, max_time=max_time, min_time=min_time)
        params_dict = params.model_dump()
        params_dict["a_bogus"] = self.get_abogus(params_dict)
        url = self.urls.FOLLOWING_LIST + self.dict_to_url_params(params_dict)
        res = requests.get(url=url, headers=self.headers)
        # with open("following_list.json", "w", encoding="utf-8") as f:
        #     f.write(res.text)
        return me_following.Base(**res.json())
        # print(res.text)cl

    def get_following_list(self, sec_user_id, user_id, offset: int = 0, count: int = 20):
        params = schemas.Following(
            sec_user_id=sec_user_id, user_id=user_id, offset=offset, count=count)
        res = self.get(self.urls.FOLLOWING, params)
        if res.status_code == 200 and res.text != "":
            # print(res.text)
            return following.Base(**res.json())
        return None

    def get_host_list(self, board_type: int = 0, board_sub_type: int | None = None):
        params = schemas.HotList(board_type=board_type,
                                 board_sub_type=board_sub_type)
        res = self.get(self.urls.HOT_LIST, params)
        if res.status_code == 200 and res.text != "":
            # print(res.text)
            return hot_list.Base(**res.json())
        return None

    def get_creator_video_list(self, sec_user_id: str, count: int = 20, max_cursor: int = 0):
        params = schemas.CreatorVideoList(
            sec_user_id=sec_user_id, count=count, max_cursor=max_cursor)
        res = self.get(self.urls.USER_POST, params)
        if res.status_code == 200 and res.text != "":
            # print(res.text)
            return video_info.Base(**res.json())
        return None

    def get(self, url, params):
        params_dict = params.model_dump()
        params_dict["a_bogus"] = self.get_abogus(params_dict)
        new_url = url + self.dict_to_url_params(params_dict)
        res = requests.get(url=new_url, headers=self.headers, timeout=10)
        return res

    def get_aweme_id(self, share_url: str):
        r = requests.get(share_url, headers={
                         "Content-Type": "application/json"})
        reditList = r.history  # 可以看出获取的是一个地址序列
        # print(f'获取重定向的历史记录：{reditList}')
        # print(f'获取第一次重定向的headers头部信息：{reditList[0].headers}')
        if len(reditList) > 0:
            url = reditList[len(reditList)-1].headers["location"]
        else:
            url = share_url
        video_pattern = re.compile(r"video/([^/?]*)")
        note_pattern = re.compile(r"note/([^/?]*)")
        match = video_pattern.search(str(url))
        if video_pattern.search(str(url)):
            aweme_id = match.group(1)
            return aweme_id
        else:
            match = note_pattern.search(str(url))
            if note_pattern.search(str(url)):
                aweme_id = match.group(1)
                return aweme_id
        return 0
        # print(f'获取重定向最终的url：{reditList[len(reditList)-1].headers["location"]}')

    def get_sec_user_id(self, share_url: str):
        r = requests.get(share_url, headers={
                         "Content-Type": "application/json"})
        reditList = r.history  # 可以看出获取的是一个地址序列
        # print(f'获取重定向的历史记录：{reditList}')
        # print(f'获取第一次重定向的headers头部信息：{reditList[0].headers}')
        if len(reditList) > 0:
            url = reditList[len(reditList)-1].headers["location"]
        else:
            url = share_url
        pattern = re.compile(r"user/([^/?]*)")
        match = pattern.search(str(url))
        if match:
            sec_user_id = match.group(1)
            return sec_user_id
        return 0

    def fetch_one_video(self, aweme_id: str) -> fetch_one_video.Base | None:
        params = schemas.FetchOneVideo(aweme_id=aweme_id)
        res = self.get(self.urls.POST_DETAIL, params)
        if res.status_code == 200 and res.text != "":
            return fetch_one_video.Base(**res.json())
        return None

    @staticmethod
    def get_abogus(url_params: dict):
        bogus = ABogus()
        # USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        # print(f"URL参数: {url_params}")
        a_bogus = bogus.get_value(url_params, )
        # 使用url编码a_bogus
        a_bogus = quote(a_bogus, safe='')
        return a_bogus

    @staticmethod
    def get_info_from_url(url, pattern):
        response = requests.get(url, allow_redirects=True)
        if response.status_code in {200, 444}:
            match = pattern.search(response.url)
            if match:
                return match.group(1)

    @staticmethod
    def dict_to_url_params(params_dict):
        if not params_dict:
            return ""

        # Create a list of key=value strings
        params_list = [f"{key}={value}" for key, value in params_dict.items()]

        # Join the list with '&' to form the final URL parameters string
        url_params = "&".join(params_list)

        return url_params
    
    
if __name__ == "__main__":
    import json
    cookie = open("douyin_cookies.txt", "r").read()
    tiktokapi = TikTokApi(cookie=cookie)
    offset = 0
    # following_list = tiktokapi.get_following_list('MS4wLjABAAAAC-l4hckaxRjVpuDxixrG3sjg-ldxhQj4Mp9ric1HC88','470245126964574', offset)
    # print(following_list.model_dump_json())
    print(tiktokapi.get_me_following_list(count=5,max_time=1725961900).model_dump_json())
    # sec_user_id = tiktokapi.get_sec_user_id("https://v.douyin.com/iUSSpMW2/")
    # print(sec_user_id)
    # data = tiktokapi.get_creator_video_list(sec_user_id, count=5)
    # # 将数据转换为JSON格式
    # json_data = data.model_dump()
    # # 保存到本地文件
    # with open('creator_videos.json', 'w', encoding='utf-8') as f:
    #     json.dump(json_data, f, ensure_ascii=False, indent=4)
    # print(f"数据已保存到 creator_videos.json 文件中")


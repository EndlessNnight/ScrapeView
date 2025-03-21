#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
@FileName   : urls.py
@Project    : apiproxy
@Description: 
@Author     : imgyh
@Mail       : admin@imgyh.com
@Github     : https://github.com/imgyh
@Site       : https://www.imgyh.com
@Date       : 2023/5/12 15:04
@Version    : v1.0
@ChangeLog 
------------------------------------------------

------------------------------------------------
'''


class Urls(object):
    def __init__(self):
        ######################################### WEB #########################################
        # 首页推荐
        self.TAB_FEED = 'https://www.douyin.com/aweme/v1/web/tab/feed/?'

        # 用户短信息（给多少个用户secid就返回多少的用户信息）
        self.USER_SHORT_INFO = 'https://www.douyin.com/aweme/v1/web/im/user/info/?'

        # 用户详细信息
        self.USER_DETAIL = 'https://www.douyin.com/aweme/v1/web/user/profile/other/?'

        # 用户作品
        self.USER_POST = 'https://www.douyin.com/aweme/v1/web/aweme/post/?'

        # 作品信息
        self.POST_DETAIL = 'https://www.douyin.com/aweme/v1/web/aweme/detail/?'

        # 用户喜欢A
        # 需要 odin_tt
        self.USER_FAVORITE_A = 'https://www.douyin.com/aweme/v1/web/aweme/favorite/?'

        # 用户喜欢B
        self.USER_FAVORITE_B = 'https://www.iesdouyin.com/web/api/v2/aweme/like/?'

        # 用户历史
        self.USER_HISTORY = 'https://www.douyin.com/aweme/v1/web/history/read/?'

        # 用户收藏
        self.USER_COLLECTION = 'https://www.douyin.com/aweme/v1/web/aweme/listcollection/?'

        # 用户评论
        self.COMMENT = 'https://www.douyin.com/aweme/v1/web/comment/list/?'

        # 用户评论回复
        self.COMMENT_REPLY = 'https://www.douyin.com/aweme/v1/web/comment/list/reply/?'

        # 首页朋友作品
        self.FRIEND_FEED = 'https://www.douyin.com/aweme/v1/web/familiar/feed/?'

        # 关注用户作品
        self.FOLLOW_FEED = 'https://www.douyin.com/aweme/v1/web/follow/feed/?'

        # 合集下所有作品
        # 只需要X-Bogus
        self.USER_MIX = 'https://www.douyin.com/aweme/v1/web/mix/aweme/?'

        # 用户所有合集列表
        # 需要 ttwid
        self.USER_MIX_LIST = 'https://www.douyin.com/aweme/v1/web/mix/list/?'

        # 直播
        self.LIVE = 'https://live.douyin.com/webcast/room/web/enter/?'
        self.LIVE2 = 'https://webcast.amemv.com/webcast/room/reflow/info/?'

        # 音乐
        self.MUSIC = 'https://www.douyin.com/aweme/v1/web/music/aweme/?'

        # 用户关注列表
        self.FOLLOWING = 'https://www.douyin.com/aweme/v1/web/user/following/list/?'
        
        # 搜索用户
        self.SEARCH_USER = 'https://www.douyin.com/aweme/v1/web/discover/search/?'
        
        # 搜索视频
        self.SEARCH_VIDEO = 'https://www.douyin.com/aweme/v1/web/search/item/?'
        
        # 抖音热榜
        self.HOT_LIST = 'https://www.douyin.com/aweme/v1/web/hot/search/list/?'

        # 用户关注列表数据
        self.FOLLOWING_LIST = 'https://www.douyin.com/aweme/v1/web/im/spotlight/relation/?'

        #######################################################################################


if __name__ == '__main__':
    pass

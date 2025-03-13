from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import re

from pydantic import BaseModel, Field

class TorrentInfo(BaseModel):
    """种子基本信息"""
    torrent_id: int
    title: str
    subtitle: str = ""
    cover_url: Optional[str] = None
    tags: List[str] = []
    discount: Optional[str] = None
    free_until: Optional[datetime] = None
    size: str
    seeders: int
    leechers: int
    up_time: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "torrent_id": 1,
                "title": "The Best Thing 2025 S01 E17-E18 2160p IQ WEB-DL H265 DDP5.1-PTerWEB",
                "subtitle": "爱你/爱上你是我做过最好的事 第17-18集 | 导演: 车亮逸 主演: 张凌赫 徐若晗 王宥钧 [国语/中字]",
                "cover_url": "https://img9.doubanio.com/view/photo/l_ratio_poster/public/p2918882215.jpg",
                "tags": ["官方", "国语", "中字"],
                "discount": "免费",
                "free_until": "2025-03-06T07:43:28",
                "size": "2.42GB",
                "seeders": 1,
                "leechers": 45,
                "up_time": "2025-03-06T07:43:28"
            }
        } 
        

def get_data(html_txt: str) -> List[TorrentInfo]:
    soup = BeautifulSoup(html_txt, 'html.parser')
    torrents = []
    
    # 查找所有种子行 - 修正选择器
    rows = soup.select('table.torrents > tr:not(:first-child)')
    
    for row in rows:
        # 跳过分页行
        if 'nexus-pagination' in row.get('class', []):
            continue
            
        # 提取种子ID和标题
        title_link = row.select_one('a[href^="details.php?id="]')
        if not title_link:
            continue
            
        torrent_id = 0
        torrent_id_match = re.search(r'id=(\d+)', title_link['href'])
        if torrent_id_match:
            torrent_id = int(torrent_id_match.group(1))
        
        title = title_link.text.strip()
        
        # 提取标签
        tags = []
        tag_elements = row.select('span[class^="tags t"]')
        for tag in tag_elements:
            tag_text = tag.text.strip()
            if tag_text:
                tags.append(tag_text)

        # 提取副标题 - 使用更精确的方法
        subtitle = ""
        subtitle_span = row.select_one('span[style*="float:left;padding: 2px;line-height: 20px;"]')
        if subtitle_span:
            subtitle = subtitle_span.text.strip()
        
        # 检查是否免费
        discount = None
        free_until = None
        free_img = row.select_one('img.pro_free')
        if free_img:
            discount = "免费"
            # 提取免费截止时间
            free_time_span = row.select_one('span[title^="202"]')
            if free_time_span and 'title' in free_time_span.attrs:
                try:
                    free_until_str = free_time_span['title']
                    free_until = datetime.strptime(free_until_str, '%Y-%m-%d %H:%M:%S')
                except (ValueError, KeyError):
                    pass
        
        # 提取大小
        size = ""
        size_td = row.select_one('td.rowfollow:nth-of-type(5)')
        if size_td:
            size = size_td.text.strip().replace('\n', ' ')
        
        # 提取上传人数(seeders)
        seeders = 0
        seeders_td = row.select_one('td.rowfollow[align="center"]')
        if seeders_td:
            seeders_a = seeders_td.select_one('b > a')
            if seeders_a:
                try:
                    seeders = int(seeders_a.text.strip())
                except ValueError:
                    pass
        
        # 提取下载人数(leechers)
        leechers = 0
        leechers_td = row.select_one('td.rowfollow:nth-of-type(7)')
        if leechers_td:
            leechers_a = leechers_td.select_one('b > a')
            if leechers_a:
                try:
                    leechers = int(leechers_a.text.strip())
                except ValueError:
                    pass
            else:
                # 如果没有链接，直接获取文本
                leechers_text = leechers_td.text.strip()
                if leechers_text and leechers_text.isdigit():
                    leechers = int(leechers_text)
        
        # 提取上传时间
        up_time = None
        time_span = row.select_one('td.rowfollow.nowrap > span[title]')
        if not time_span:
            time_span = row.select_one('td.rowfollow:nth-of-type(4) span[title]')
        
        if time_span and 'title' in time_span.attrs:
            try:
                time_str = time_span['title']
                up_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            except (ValueError, KeyError):
                pass
        
        # 提取封面URL - 这个站点可能没有直接显示封面
        cover_url = None
        img_element = row.select_one('img.lozad[data-orig]')
        if img_element and 'data-orig' in img_element.attrs:
            cover_url = img_element['data-orig']
        
        # 创建TorrentInfo对象
        torrent_info = TorrentInfo(
            torrent_id=torrent_id,
            title=title,
            subtitle=subtitle,
            cover_url=cover_url,
            tags=tags,
            discount=discount,
            free_until=free_until,
            size=size,
            seeders=seeders,
            leechers=leechers,
            up_time=up_time
        )
        
        torrents.append(torrent_info)
    
    return torrents

if __name__ == "__main__":
    try:
        with open('response.html', 'r', encoding='utf-8') as f:
            html_txt = f.read()
            torrents = get_data(html_txt)
            print(f"成功解析到 {len(torrents)} 个种子")
            for torrent in torrents:
                print(f"ID: {torrent.torrent_id}, 标题: {torrent.title}")
                print(f"副标题: {torrent.subtitle}")
                print(f"标签: {torrent.tags}")
                print(f"大小: {torrent.size}, 做种: {torrent.seeders}, 下载: {torrent.leechers}")
                print("-" * 50)
    except Exception as e:
        print(f"解析出错: {str(e)}")

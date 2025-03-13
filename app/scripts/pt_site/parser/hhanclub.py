from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
from ..base import BaseSiteParser
from ..schemas import TorrentInfo, TorrentDetails, PTUserInfo, TorrentInfoList
import json

class HHAnClubParser(BaseSiteParser):
    """HDFans框架PT站点解析器"""
    
    def __init__(self):
        # 魔力值匹配模式
        self.bonus_patterns = [
            r'站免池.*?]:\s*([\d,]+\.?\d*)',  # 模式1: 站免池
            r'魔力值.*?]:\s*([\d,]+\.?\d*)',   # 模式2: 魔力值
            r'爆米花系统.*?]?\s*:\s*([\d,]+\.?\d*)',  # 模式3: 爆米花系统
            r'使用.*?]:\s*([\d,]+\.?\d*)',     # 模式4: 使用
            r'魔力值.*?:\s*([\d,]+\.?\d*)',    # 模式5: 魔力值（无方括号）
            r'魔力.*?:\s*([\d,]+\.?\d*)',      # 模式6: 简化魔力
            r'bonus.*?:\s*([\d,]+\.?\d*)',     # 模式7: bonus关键字
            r'积分.*?:\s*([\d,]+\.?\d*)'       # 模式8: 积分关键字
        ]
        
        # 文件大小匹配模式
        self.size_pattern = r'([\d.]+)\s*(TB|GB|MB|KB|B)'
    
    def _clean_text(self, text: str) -> str:
        """清理文本中的特殊字符"""
        return ''.join(text.split())
    
    def _extract_number(self, text: str, pattern: str) -> float:
        """从文本中提取数字"""
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(',', ''))
        return 0.0
    
    def _parse_size(self, size_text: str) -> str:
        """解析文件大小"""
        if not size_text:
            return "0 B"
        match = re.search(self.size_pattern, size_text)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        return "0 B"
    
    def _extract_username(self, elem) -> str:
        """提取并处理用户名"""
        try:
            if not elem:
                return "Unknown"
            username = elem.get_text(strip=True)
            # 只保留字母、数字、空格和中文字符
            return re.sub(r'[^\w\s\u4e00-\u9fff]', '', username)
        except Exception as e:
            print(f"用户名解析错误: {str(e)}")
            return "Unknown"
    
    def _extract_bonus(self, table, text_content: str) -> float:
        """提取魔力值"""
        bonus = 0.0
        
        # 方法1: 从class="color_bonus"元素获取
        bonus_elem = table.find(class_="color_bonus")
        if bonus_elem and bonus_elem.next_sibling:
            bonus_text = bonus_elem.next_sibling.strip()
            bonus_match = re.search(r'([\d,]+\.?\d*)', bonus_text)
            if bonus_match:
                return float(bonus_match.group(1).replace(',', ''))
        
        # 方法2: 使用正则表达式模式
        for pattern in self.bonus_patterns:
            bonus_match = re.search(pattern, text_content, re.DOTALL | re.IGNORECASE)
            if bonus_match:
                return float(bonus_match.group(1).replace(',', ''))
        
        return bonus
    
    def _extract_stats(self, table) -> tuple[float, str, str, int, int]:
        """提取用户统计数据"""
        text_content = table.get_text()
        
        # 提取分享率
        ratio = 0.0
        ratio_elem = table.find(class_="color_ratio")
        if ratio_elem and ratio_elem.next_sibling:
            ratio_text = ratio_elem.next_sibling.strip()
            if ratio_text == "无限":
                ratio = 999.0
            else:
                try:
                    ratio = float(ratio_text)
                except ValueError:
                    ratio = 0.0
        
        # 提取上传下载量
        uploaded = "0 B"
        downloaded = "0 B"
        uploaded_elem = table.find(class_="color_uploaded")
        downloaded_elem = table.find(class_="color_downloaded")
        
        if uploaded_elem and uploaded_elem.next_sibling:
            uploaded = self._parse_size(uploaded_elem.next_sibling.strip())
        if downloaded_elem and downloaded_elem.next_sibling:
            downloaded = self._parse_size(downloaded_elem.next_sibling.strip())
        
        # 提取做种和下载数
        seeding = 0
        leeching = 0
        active_pattern = r'当前活动.*?(\d+).*?(\d+)'
        active_match = re.search(active_pattern, text_content, re.DOTALL)
        if active_match:
            seeding = int(active_match.group(1))
            leeching = int(active_match.group(2))
        
        return ratio, uploaded, downloaded, seeding, leeching
    
    def parse_torrent_list(self, soup: BeautifulSoup) -> TorrentInfoList:
        """解析种子列表页面"""
        torrents = TorrentInfoList()
        # 查找种子列表容器
        torrent_container = soup.select_one('div.torrent-table-for-spider')
        if not torrent_container:
            return torrents
            
        # 查找所有种子项
        for torrent_item in torrent_container.select('div.torrent-table-sub-info'):
            try:
                # 获取种子ID和标题
                title_link = torrent_item.select_one('a.torrent-info-text-name')
                if not title_link:
                    continue
                    
                title = title_link.text.strip()
                torrent_id = int(title_link['href'].split('id=')[1].split('&')[0])
                
                # 获取副标题
                subtitle_elem = torrent_item.select_one('div.torrent-info-text-small_name')
                subtitle = subtitle_elem.text.strip() if subtitle_elem else ""
                
                # 获取标签
                tags = []
                tag_spans = torrent_item.select('span.tag')
                for span in tag_spans:
                    tags.append(span.text.strip())
                
                # 获取封面图片 - 在这个网站上可能没有直接的封面图片
                cover_url = None
                
                # 获取折扣信息
                discount = None
                promotion_span = torrent_item.select_one('span.promotion-tag')
                if promotion_span:
                    if 'promotion-tag-free' in promotion_span.get('class', []):
                        discount = '免费'
                    elif 'promotion-tag-50' in promotion_span.get('class', []):
                        discount = '50%'
                    elif 'promotion-tag-30' in promotion_span.get('class', []):
                        discount = '30%'
                    elif 'promotion-tag-2xfree' in promotion_span.get('class', []):
                        discount = '2x免费'
                    else:
                        discount = promotion_span.text.strip()
                
                # 获取免费时间
                free_until = None
                free_time_span = torrent_item.select_one('span:-soup-contains("剩余时间") span[title]')
                if free_time_span and free_time_span.has_attr('title'):
                    try:
                        free_until_text = free_time_span.get('title')
                        if free_until_text:
                            free_until = datetime.strptime(free_until_text, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        pass
                
                # 获取大小
                size_elem = torrent_item.select_one('div.torrent-info-text-size')
                size = size_elem.text.strip() if size_elem else "0 B"
                
                # 获取做种数和下载数
                seeders_elem = torrent_item.select_one('div.torrent-info-text-seeders')
                leechers_elem = torrent_item.select_one('div.torrent-info-text-leechers')
                
                seeders = 0
                if seeders_elem:
                    seeders_link = seeders_elem.select_one('a')
                    if seeders_link:
                        seeders = int(seeders_link.text.strip())
                    else:
                        seeders = int(seeders_elem.text.strip())
                
                leechers = 0
                if leechers_elem:
                    leechers = int(leechers_elem.text.strip())
                
                # 获取完成数
                finished = 0
                finished_elem = torrent_item.select_one('div.torrent-info-text-finished')
                if finished_elem:
                    finished_link = finished_elem.select_one('a')
                    if finished_link:
                        finished = int(finished_link.text.strip())
                    else:
                        try:
                            finished = int(finished_elem.text.strip())
                        except ValueError:
                            finished = 0
                
                # 获取上传时间
                up_time = None
                time_span = torrent_item.select_one('div.torrent-info-text-added span[title]')
                if time_span and time_span.has_attr('title'):
                    try:
                        up_time = datetime.strptime(time_span['title'], '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        pass
                
                torrent = TorrentInfo(
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
                    up_time=up_time,
                    finished=finished
                )
                torrents.torrents.append(torrent)
            except Exception as e:
                print(f"解析种子数据时出错: {str(e)}")
                continue
                
        return torrents

    def parse_torrent_detail(self, soup: BeautifulSoup) -> TorrentDetails:
        """解析种子详情页面"""
        try:
            # 获取标题
            title_div = soup.select_one('div.font-bold.leading-6:-soup-contains("标题") + div.font-bold.leading-6')
            title = title_div.text.strip() if title_div else ""
            
            # 如果找不到标题，尝试从页面标题获取
            if not title:
                page_title = soup.select_one('title')
                if page_title:
                    title_match = re.search(r'种子详情 "([^"]+)"', page_title.text)
                    if title_match:
                        title = title_match.group(1)
            
            # 获取副标题
            subtitle_div = soup.select_one('div.font-bold.leading-6:-soup-contains("副标题") + div.font-bold.leading-6')
            subtitle = subtitle_div.text.strip() if subtitle_div else ""
            
            # 获取基本信息
            info_text = ""
            info_div = soup.select_one('div.font-bold.leading-6:-soup-contains("基本信息") + div.grid')
            if info_div:
                info_text = info_div.text.strip()
            
            # 获取同伴信息（做种人数和下载人数）
            peers_info = ""
            seeders = 0
            leechers = 0
            
            # 使用 div id=seeder-count 和 div id=leecher-count 获取做种人数和下载人数
            seeders_div = soup.select_one('div#seeder-count')
            leechers_div = soup.select_one('div#leecher-count')
            
            if seeders_div:
                try:
                    seeders = int(re.search(r'\d+', seeders_div.text).group())
                except (AttributeError, ValueError):
                    pass
                    
            if leechers_div:
                try:
                    leechers = int(re.search(r'\d+', leechers_div.text).group())
                except (AttributeError, ValueError):
                    pass
                    
            peers_info = f"做种: {seeders}, 下载: {leechers}"
            
            # 获取简介内容 - 只获取 div id=screenshot-content 内部的图片
            descr_images = []
            
            # 查找 screenshot-content div
            screenshot_div = soup.select_one('div#screenshot-content')
            if screenshot_div:
                # 获取 div 内部的所有图片
                img_tags = screenshot_div.select('img')
                for img in img_tags:
                    if img.get('src'):
                        descr_images.append(img.get('src'))
            
            # 获取折扣信息
            discount = None
            promotion_span = soup.select_one('span.promotion-tag')
            if promotion_span:
                if 'promotion-tag-free' in promotion_span.get('class', []):
                    discount = '免费'
                elif 'promotion-tag-50' in promotion_span.get('class', []):
                    discount = '50%'
                elif 'promotion-tag-30' in promotion_span.get('class', []):
                    discount = '30%'
                elif 'promotion-tag-2xfree' in promotion_span.get('class', []):
                    discount = '2x免费'
                else:
                    discount = promotion_span.text.strip()
            
            # 获取免费时间
            free_until = None
            free_time_span = soup.select_one('span:-soup-contains("剩余时间") span[title]')
            if free_time_span and free_time_span.has_attr('title'):
                try:
                    free_until_text = free_time_span.get('title')
                    if free_until_text:
                        free_until = datetime.strptime(free_until_text, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass
                    
            return TorrentDetails(
                title=title,
                subtitle=subtitle,
                descr_images=descr_images,
                peers_info=peers_info,
                info_text=info_text,
                discount=discount,
                free_until=free_until,
                seeders=seeders,
                leechers=leechers
            )
        except Exception as e:
            print(f"解析种子详情时出错: {str(e)}")
            return TorrentDetails(
                title="",
                subtitle="",
                descr_images=[],
                peers_info="",
                info_text=""
            )

    def parse_user_info(self, soup: BeautifulSoup) -> PTUserInfo:
        """解析用户信息页面"""
        try:
            # 查找用户信息面板
            user_panel = soup.select_one('div#user-info-panel')
            if not user_panel:
                raise ValueError("未找到用户信息面板")
            
            # 提取用户名
            username_elem = user_panel.select_one('a.VeteranUser_Name > b')
            username = username_elem.text.strip() if username_elem else ""
            
            # 提取魔力值（憨豆）
            bonus = 0
            bonus_elem = user_panel.select_one('img[alt="憨豆"] + a div')
            if bonus_elem:
                bonus_text = bonus_elem.text.strip().replace(',', '')
                try:
                    bonus = float(bonus_text)
                except ValueError:
                    pass
            
            # 提取分享率
            ratio = 0
            ratio_elem = user_panel.select_one('img[alt="分享率"] + div')
            if ratio_elem:
                ratio_match = re.search(r'(\d+\.\d+)', ratio_elem.text)
                if ratio_match:
                    try:
                        ratio = float(ratio_match.group(1))
                    except ValueError:
                        pass
            
            # 提取上传量
            uploaded = ""
            # 直接查找包含上传图标的 div
            uploaded_div = user_panel.select_one('div.text-sm.flex.items-center.justify-start > img[alt="上传"]')
            if uploaded_div and uploaded_div.parent:
                # 获取父元素的文本内容
                uploaded_text = uploaded_div.parent.get_text(strip=True)
                # 使用正则表达式提取上传量
                uploaded_match = re.search(r'(\d+\.\d+\s*[TGM]B)', uploaded_text)
                if uploaded_match:
                    uploaded = uploaded_match.group(1)
            
            # 提取下载量
            downloaded = ""
            downloaded_elem = user_panel.select_one('img[alt="下载"] + text, div:-soup-contains("下载") img[alt="下载"]')
            if downloaded_elem:
                # 使用正则表达式提取下载量
                downloaded_match = re.search(r'(\d+\.\d+\s*[TGM]B)', downloaded_elem.parent.text)
                if downloaded_match:
                    downloaded = downloaded_match.group(1)
            
            # 提取做种数
            seeding = 0
            seeding_elem = user_panel.select_one('img[alt="做种数"]')
            if seeding_elem and seeding_elem.parent:
                seeding_text = seeding_elem.parent.text
                seeding_match = re.search(r'(\d+)', seeding_text)
                if seeding_match:
                    try:
                        seeding = int(seeding_match.group(1))
                    except ValueError:
                        pass
            
            # 提取下载数
            leeching = 0
            leeching_elem = user_panel.select_one('img[alt="下载数"]')
            if leeching_elem and leeching_elem.parent:
                leeching_text = leeching_elem.parent.text
                leeching_match = re.search(r'(\d+)', leeching_text)
                if leeching_match:
                    try:
                        leeching = int(leeching_match.group(1))
                    except ValueError:
                        pass
            
            return PTUserInfo(
                username=username,
                bonus=bonus,
                ratio=ratio,
                uploaded=uploaded,
                downloaded=downloaded,
                seeding=seeding,
                leeching=leeching
            )
        except Exception as e:
            print(f"解析用户信息时出错: {str(e)}")
            return PTUserInfo(
                username="",
                bonus=0,
                ratio=0,
                uploaded="",
                downloaded="",
                seeding=0,
                leeching=0
            )


def main():
    with open("response.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
        parser = HHAnClubParser()
        details = parser.parse_user_info(soup)
        print(details.model_dump_json())

if __name__ == "__main__":
    main()
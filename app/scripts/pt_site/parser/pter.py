from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
from ..base import BaseSiteParser
from ..schemas import TorrentInfo, TorrentDetails, PTUserInfo, TorrentInfoList
import json

class PterParser(BaseSiteParser):
    """PterClub框架PT站点解析器"""
    
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
            ratio = float(ratio_elem.next_sibling.strip())
        
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
        torrents_table = soup.select_one('table.torrents')
        if not torrents_table:
            return torrents
        for torrent_row in torrents_table.select('tr:has(td.rowfollow)'):
            try:
                # 获取标题和副标题
                title_div = torrent_row.select_one('td.embedded div')
                title = title_div.select_one('div:nth-child(1) a[title]')['title']
                torrent_id = int(title_div.select_one('div:nth-child(1) a[title]')['href'].split('id=')[-1])
                                            
                # 获取副标题
                subtitle_span = title_div.select_one('div:nth-child(2) span')
                if subtitle_span:
                    subtitle = subtitle_span.text.strip()
                else:
                    subtitle_div = title_div.select_one('div:nth-child(2)')
                    if subtitle_div:
                        for tag in subtitle_div.select('a'):
                            tag.decompose()
                        subtitle = subtitle_div.text.strip()
                    else:
                        subtitle = ""

                # 获取封面图片
                cover_img = torrent_row.select_one('img.lozad')
                cover_url = cover_img['data-orig'] if cover_img else None

                # 获取标签
                tags = [tag.text.strip() for tag in torrent_row.select('a.chs_tag')]

                # 获取折扣信息
                discount_img = torrent_row.select_one('img.pro_free, img.pro_50pctdown')
                discount = None
                if discount_img:
                    if 'pro_free' in discount_img.get('class', []):
                        discount = '免费'
                    elif 'pro_50pctdown' in discount_img.get('class', []):
                        discount = '50%'

                # 获取免费时间
                free_until = None
                free_time_span = title_div.select_one('div:nth-child(1) span[title]')
                if free_time_span:
                    try:
                        free_until = datetime.strptime(free_time_span['title'], '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        pass
                
                # 获取其他信息
                rowfollow_list = torrent_row.select('td.rowfollow')
                # 上传时间
                up_time = None
                try:
                    up_time = datetime.strptime(rowfollow_list[3].select_one('span')['title'], '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError, IndexError):
                    pass
                
                size = rowfollow_list[4].text.strip() if len(rowfollow_list) > 4 else "0 B"
                seeders = int(rowfollow_list[5].text.strip()) if len(rowfollow_list) > 5 else 0
                leechers = int(rowfollow_list[6].text.strip()) if len(rowfollow_list) > 6 else 0
                
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
                )
                torrents.torrents.append(torrent)
            except Exception as e:
                print(f"解析种子数据时出错: {str(e)}")
                continue
                
        return torrents

    def parse_torrent_detail(self, soup: BeautifulSoup) -> TorrentDetails:
        """解析种子详情页面"""
        # 获取标题
        title = soup.select_one('#top').text.strip()
        
        # 获取副标题
        subtitle_row = soup.find('td', {'class': 'rowhead', 'valign': 'top', 'align': 'right'}, string='副标题')
        subtitle = ""
        if subtitle_row and subtitle_row.find_next_sibling('td'):
            subtitle = subtitle_row.find_next_sibling('td').text.strip()
        
        # 获取基本信息
        info_text = ""
        basic_info_row = soup.find('td', {'class': 'rowhead', 'valign': 'top', 'align': 'right'}, string='基本信息')
        if basic_info_row and basic_info_row.find_next_sibling('td'):
            info_text = basic_info_row.find_next_sibling('td').text.strip()
        
        # 获取同伴信息
        peers_info = ""
        peers_row = soup.find('td', {'class': 'rowhead', 'valign': 'top', 'align': 'right'}, string='同伴')
        if peers_row and peers_row.find_next_sibling('td'):
            peers_info = peers_row.find_next_sibling('td').text.strip()
            peers_info = peers_info.replace('[查看列表]', '').strip()
        
        # 获取简介内容 - 只获取图片
        descr_images = []
        descr_div = soup.select_one('#kdescr')
        if descr_div:
            images = descr_div.find_all('img')
            if images:
                for img in images:
                    if img.get('src'):
                        descr_images.append(img.get('src'))
                        
        return TorrentDetails(
            title=title,
            subtitle=subtitle,
            descr_images=descr_images,
            peers_info=peers_info,
            info_text=info_text
        )

    def parse_user_info(self, soup: BeautifulSoup) -> PTUserInfo:
        """解析用户信息页面"""
        try:
            table = soup.select_one('#info_block').select(".bottom")[0]
            
            # 提取用户名
            username = self._extract_username(table.select_one('.nowrap > a'))
            
            # 提取魔力值
            bonus = self._extract_bonus(table, table.get_text())
            
            # 提取其他统计数据
            ratio, uploaded, downloaded, seeding, leeching = self._extract_stats(table)
            
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
            print(f"解析错误: {str(e)}")
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
        parser = PterParser()
        details = parser.parse_torrent_list(soup)
        print(details.model_dump_json())

if __name__ == "__main__":
    main()
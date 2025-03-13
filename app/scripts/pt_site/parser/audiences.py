from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
from ..base import BaseSiteParser
from ..schemas import TorrentInfo, TorrentDetails, PTUserInfo, TorrentInfoList
import json

class AudiencesParser(BaseSiteParser):
    """Audiences框架PT站点解析器"""
    
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
        
        # 1. 查找种子表格
        torrents_table = soup.select_one('table.torrents')
        if not torrents_table:
            return torrents
        
        # 2. 遍历每一行种子数据
        for row in torrents_table.select('tr:has(td.rowfollow)'):
            try:
                # 3. 提取基本信息
                torrent = self._parse_torrent_row(row)
                if torrent:
                    torrents.torrents.append(torrent)
            except Exception as e:
                print(f"解析种子行时出错: {str(e)}")
                continue
        
        return torrents
    
    def _parse_torrent_row(self, row) -> Optional[TorrentInfo]:
        """解析单行种子数据"""
        # 1. 获取种子名称表格
        name_table = row.select_one('table.torrentname')
        if not name_table:
            return None
        
        embedded_td = name_table.select_one('td.embedded')
        if not embedded_td:
            return None
        
        # 2. 提取标题和ID
        title_link = embedded_td.select_one('a[title]')
        if not title_link:
            return None
        
        title = title_link['title']
        try:
            torrent_id = int(title_link['href'].split('id=')[-1].split('&')[0])
        except (ValueError, IndexError):
            return None
        
        # 3. 提取标签
        tags = []
        for tag in embedded_td.select('span.tags'):
            # if tag.get('title'):
                # tags.append(tag.get('title'))
            # elif tag.text.strip():
            tags.append(tag.text.strip())
        
        # 4. 提取副标题
        subtitle = ""
        subtitle_span = embedded_td.select_one('span[style*="padding: 2px;line-height: 20px;"]')
        if subtitle_span:
            subtitle = subtitle_span.text.strip()
        
        # 5. 提取折扣信息
        discount = None
        if embedded_td.select_one('img.pro_free'):
            discount = '免费'
        elif embedded_td.select_one('img.pro_50pctdown'):
            discount = '50%'
        
        # 6. 提取免费截止时间
        free_until = None
        free_time_span = embedded_td.select_one('span[title*="-"]')
        if free_time_span and free_time_span.get('title'):
            try:
                free_until = datetime.strptime(free_time_span['title'], '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                pass
        
        # 7. 提取其他信息
        cells = row.select('td.rowfollow')
        
        # 上传时间
        up_time = self._extract_upload_time(cells)
        
        # 大小
        size = self._extract_size(cells)
        
        # 做种数和下载数
        seeders = self._extract_seeders(cells)
        leechers = self._extract_leechers(cells)
        
        # 8. 创建TorrentInfo对象
        return TorrentInfo(
            torrent_id=torrent_id,
            title=title,
            subtitle=subtitle,
            cover_url=None,  # 此站点没有封面图片
            tags=tags,
            discount=discount,
            free_until=free_until,
            size=size,
            seeders=seeders,
            leechers=leechers,
            up_time=up_time,
        )
    
    def _extract_upload_time(self, cells) -> Optional[datetime]:
        """提取上传时间"""
        if len(cells) <= 3:
            return None
        
        time_cell = cells[3]
        time_span = time_cell.select_one('span[title]')
        if not time_span or not time_span.get('title'):
            return None
        
        try:
            return datetime.strptime(time_span['title'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return None
    
    def _extract_size(self, cells) -> str:
        """提取大小"""
        if len(cells) <= 4:
            return "0 B"
        
        return cells[4].text.strip()
    
    def _extract_seeders(self, cells) -> int:
        """提取做种数"""
        if len(cells) <= 5:
            return 0
        
        seeders_cell = cells[5]
        seeders_text = seeders_cell.text.strip()
        
        # 处理可能的链接文本
        seeders_link = seeders_cell.select_one('a')
        if seeders_link:
            seeders_text = seeders_link.text.strip()
        
        # 提取数字
        digits = ''.join(c for c in seeders_text if c.isdigit())
        if not digits:
            return 0
        
        try:
            return int(digits)
        except ValueError:
            return 0
    
    def _extract_leechers(self, cells) -> int:
        """提取下载数"""
        if len(cells) <= 6:
            return 0
        
        leechers_text = cells[6].text.strip()
        digits = ''.join(c for c in leechers_text if c.isdigit())
        if not digits:
            return 0
        
        try:
            return int(digits)
        except ValueError:
            return 0

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
    with open("test_html/audiences_list.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
        parser = AudiencesParser()
        details = parser.parse_torrent_list(soup)
        for detail in details:
            try:
                print(detail.model_dump_json())
            except Exception as e:
                print(f"输出种子信息时出错: {str(e)}")
                print(f"种子ID: {detail.torrent_id}, 标题: {detail.title}")

if __name__ == "__main__":
    main()
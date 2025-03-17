from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
from ..base import BaseSiteParser
from ..schemas import TorrentInfo, TorrentDetails, PTUserInfo, TorrentInfoList, ParseTableTitle

class AzusaParser(BaseSiteParser):
    """Azusa框架PT站点解析器"""
    
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
        
        self.discount_tab = {
            'pro_free': '免费',
            'pro_free2up': '2X免费',
            'pro_30pctdown': '30%折扣',
            'pro_50pctdown': '50%折扣',
            'pro_50pctdown2up': '2倍50%折扣',
        }
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
    

    def _parse_table_title(self, title_elem: BeautifulSoup) -> ParseTableTitle:
        """解析种子标题"""
        tds = title_elem.select('td.embedded:not([valign])')
        cover_url = None
        title = None
        subtitle = None
        tags = []
        free_until = None
        discount = None
        cover_elem = tds[0]
        title_content_elem = tds[1] if len(tds) > 1 else None
        
        img_elem = cover_elem.select_one('img.nexus-lazy-load')
        if img_elem:
            cover_url = img_elem['data-src']
        else:
            title_content_elem = tds[0]

        if title_content_elem:
            title = title_content_elem.select_one('a')['title']
            torrent_id = title_content_elem.select_one('a')['href'].split('id=')[1].split('&')[0]
            spans = title_content_elem.select('span[style*="background-color"]')
            if len(spans) == 0:
                # hdsky 适配
                spans = title_content_elem.select('span[class="optiontag"]')
            if spans:
                for span in spans:
                    tags.append(span.text.strip())
            all_sibling_nodes = title_content_elem.contents
            last_node = all_sibling_nodes[-1]

            is_br = False
            for node in all_sibling_nodes:
                if node.name == 'br':
                    is_br = True
                if is_br and not node.name:
                    subtitle = ' '.join(node.strip().split())

            # if last_node and last_node.name == 'span':
            #     subtitle = ' '.join(last_node.text.strip().split())
            # else:
            #     subtitle = ' '.join(last_node.strip().split())
            

        imgs = title_content_elem.select('img')
        for img in imgs:
            discount_str = img.get('class')[0]
            if discount_str in self.discount_tab:
                discount = self.discount_tab[discount_str]
                fiscount_elem = title_content_elem.select_one('font > span[title]')
                if fiscount_elem:
                    free_until = fiscount_elem.get('title')
                break

        return ParseTableTitle(
            title=title,
            subtitle=subtitle,
            tags=tags,
            discount=discount,
            free_until=free_until,
            cover_url=cover_url,
            torrent_id=torrent_id
        )

    def parse_torrent_list(self, soup: BeautifulSoup) -> TorrentInfoList:
        """解析种子列表页面"""
        torrents = TorrentInfoList()
        try:
            rows = soup.select('table[class="torrents"] > tr')[1:]
            if len(rows) == 0:
                rows = soup.select('table[class="torrents progresstable"] > tr')[1:]

            for row in rows:
                cells = row.select('td.rowfollow')
                if len(cells) == 0:
                    continue
                child_0 = cells[0]
                child_1 = cells[1]
                child_2 = cells[2]
                child_3 = cells[3]
                child_4 = cells[4]
                child_5 = cells[5]

                parse_table_title = self._parse_table_title(child_1)
                
                up_time = child_3.select_one('span[title]')['title']
                size = child_4.text
                stats = child_5.text.strip().split('/')
                seeders = int(stats[0].strip().replace(',', ''))
                leechers = int(stats[1].strip().replace(',', ''))
                finished = int(stats[2].strip().replace(',', ''))

                torrent = TorrentInfo(
                    torrent_id=parse_table_title.torrent_id,
                    title=parse_table_title.title,
                    subtitle=parse_table_title.subtitle,
                    cover_url=parse_table_title.cover_url,
                    tags=parse_table_title.tags,
                    discount=parse_table_title.discount,
                    free_until=parse_table_title.free_until,
                    size=size,
                    seeders=seeders,
                    leechers=leechers,
                    up_time=up_time,
                    finished=finished
                )
                torrents.torrents.append(torrent)
        except Exception as e:
            print(f"解析错误: {str(e)}")
        return torrents

    def parse_torrent_detail(self, soup: BeautifulSoup) -> TorrentDetails:
        """解析种子详情页面"""
        outer_elem = soup.select_one("#outer")
        if not outer_elem:
            return TorrentDetails()
        

        # 获取标题
        title = outer_elem.select_one('#top').text.strip()
        # 获取副标题
        subtitle_row = outer_elem.find('td', {'class': 'rowhead', 'valign': 'top', 'align': 'right'}, string='副标题')
        subtitle = ""
        if subtitle_row and subtitle_row.find_next_sibling('td'):
            subtitle = subtitle_row.find_next_sibling('td').text.strip()
        

        torrent_name = ""
        torrent_name_row = outer_elem.find('td', {'class': 'rowhead'}, string='下载')
        if torrent_name_row and torrent_name_row.find_next_sibling('td'):
            torrent_name = torrent_name_row.find_next_sibling('td').text.strip()


        # 获取基本信息
        info_text = ""
        basic_info_row = outer_elem.find('td', {'class': 'rowhead', 'valign': 'top', 'align': 'right'}, string='基本信息')
        if basic_info_row and basic_info_row.find_next_sibling('td'):
            info_text = basic_info_row.find_next_sibling('td').text.strip()
        
        # 获取同伴信息
        peers_info = ""
        peers_row = outer_elem.select_one("div#peercount")
        if peers_row:
            peers_info = peers_row.text
        
        # 获取简介内容 - 只获取图片
        descr_images = []
        descr_div = outer_elem.select_one('#kdescr')
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
            info_text=info_text,
            torrent_name=torrent_name
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
    with open("app/scripts/pt_site/html/Azusa_list2.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
        parser = AzusaParser()
        details = parser.parse_torrent_list(soup)
        print(details.model_dump_json())
        # details = parser.parse_torrent_detail(soup)
        # print(details.model_dump_json())
            

        # user_info = parser.parse_user_info(soup)
        # print(user_info.model_dump_json())


if __name__ == "__main__":
    main()
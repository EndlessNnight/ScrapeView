from bs4 import BeautifulSoup
from typing import Dict, Union, Any, Optional
from pydantic import HttpUrl
import re
from dataclasses import dataclass
from enum import Enum

@dataclass
class PTUserInfo:
    """PT用户信息数据类"""
    username: str
    bonus: float
    ratio: float
    uploaded: str
    downloaded: str
    seeding: int
    leeching: int

class SizeUnit(Enum):
    """文件大小单位枚举"""
    B = 1
    KB = 1024
    MB = 1024 * 1024
    GB = 1024 * 1024 * 1024
    TB = 1024 * 1024 * 1024 * 1024

class NexusPHPParser:
    """NexusPHP框架PT站点解析器"""
    
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
    
    def get_user_info(self, html_content: str) -> Optional[PTUserInfo]:
        """
        解析PT站点用户信息
        
        Args:
            html_content: 包含用户信息的HTML内容
            
        Returns:
            PTUserInfo: 包含用户信息的数据类实例，解析失败时返回None
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
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
            return None

def print_user_info(user_info: PTUserInfo) -> None:
    """打印用户信息"""
    if not user_info:
        print("无法获取用户信息")
        return
        
    print(f"用户名: {user_info.username}")
    print(f"魔力值: {user_info.bonus:,.1f}")
    print(f"分享率: {user_info.ratio}")
    print(f"上传量: {user_info.uploaded}")
    print(f"下载量: {user_info.downloaded}")
    print(f"当前做种: {user_info.seeding}")
    print(f"当前下载: {user_info.leeching}")
    print("-" * 30)




html_txt = """
<table id="info_block" cellpadding="4" cellspacing="0" border="0" width="100%"><tbody><tr>
  <td><table width="100%" cellspacing="0" cellpadding="0" border="0"><tbody><tr>
    <td class="bottom" align="left">
		<span class="medium">欢迎回来, <span class="nowrap"><a href="userdetails.php?id=9565" class="VIP_Name"><b>XiaoDai</b></a><img class="star" src="pic/trans.gif" alt="Donor" style="margin-left: 2pt"> <span title="2FA"><a href="https://wiki.pterclub.com/wiki/2FA" target="_blank">🔐</a></span></span>			[<a href="#" data-url="logout.php" id="logout-confirm">退出</a>]
									[<a href="torrents.php?inclbookmarked=1&amp;allsec=1&amp;incldead=0">收藏</a>]
			[<a href="viewclaims.php">已认领种子</a>]
			<!-- [<a href="myrss.php">RSS 下载筐</a>] -->
            <a title="点击查看每小时收益预测" href="mybonus.php#bonus-sum">
                <span class="color_bonus">猫粮 </span>
            </a>
			[<a href="mybonus.php">使用</a> | <a href="sitefreepool.php">站免池</a>]: 379,962.3<span id="attendance-wrap">&nbsp;(签到已得140) </span> <font class="color_invite">邀请 </font>
		[<a href="invite.php?id=9565">发送</a>]:
		12/0<br>

		<font class="color_ratio">分享率：</font> 7.571		<font class="color_uploaded">上传量：</font>
		18.462 TB<font class="color_downloaded">
			下载量：</font> 2.438 TB		<span class="color_bonus">做种积分：</span> 2,575,596.9		<font class="color_active">当前活动：</font>
		<a href="getusertorrentlist.php?userid=9565&amp;type=seeding">
			<img class="arrowup" alt="Torrents seeding" title="当前做种" src="pic/trans.gif">
			17</a>
		<a href="getusertorrentlist.php?userid=9565&amp;type=leeching">
			<img class="arrowdown" alt="Torrents leeching" title="当前下载" src="pic/trans.gif">
            0</a>
    </span></td>

  <td class="bottom" align="right">
<div id="lang-selector">

        
          <img src="/pic/flag/china.gif" height="10" width="16" alt="简体中文" title="简体中文">&nbsp;
        
        <a href="?sitelanguage=28">  <img src="/pic/flag/hong_kong.gif" height="10" width="16" alt="轉為繁體中文" title="轉為繁體中文">&nbsp;
        </a>
        <a href="?sitelanguage=6">  <img src="/pic/flag/uk.gif" height="10" width="16" alt="Switch to English" title="Switch to English">&nbsp;
        </a>
    <span class="medium">
		    </span>
</div>
	  <span class="medium">
        <a href="messages.php"><img class="inbox" src="pic/trans.gif" alt="inbox" title="收件箱&nbsp;(无新短讯)"></a> 22 (0 新)  <a href="messages.php?action=viewmailbox&amp;box=-1"><img class="sentbox" alt="sentbox" title="发件箱" src="pic/trans.gif"></a> 4 <a href="friends.php"><img class="buddylist" alt="Buddylist" title="社交名单" src="pic/trans.gif"></a> <a href="getrss.php"><img class="rss" alt="RSS" title="获取RSS" src="pic/trans.gif"></a> <a href="contactstaff.php"><img alt="ContactStaff" title="给管理组发短讯" src="storage/uploadpicz/misc/contactstaff.png"></a>
    </span></td>
    </tr></tbody></table></td>
</tr></tbody></table>
"""

html_txt_1 = """
<table id="info_block" cellpadding="4" cellspacing="0" border="0" width="100%"><tbody><tr>
	<td><table width="100%" cellspacing="0" cellpadding="0" border="0"><tbody><tr>
		<td class="bottom" align="left">
            <span class="medium">
                欢迎回来, <span class="nowrap"><a href="https://hdfans.org/userdetails.php?id=13574" class="InsaneUser_Name"><b>XiaoDai</b></a><img src="http://img.hdfans.org/images/2023/06/01/HDFans-2021.png" title="HDFans一周年纪念勋章" class="nexus-username-medal preview" style="max-height: 11px;max-width: 11px;margin-left: 2pt"><img src="http://img.hdfans.org/images/2023/06/01/HDFans-2022.png" title="HDFans二周年纪念勋章" class="nexus-username-medal preview" style="max-height: 11px;max-width: 11px;margin-left: 2pt"><img src="http://img.hdfans.org/images/2023/06/01/HDFans-2023.png" title="HDFans三周年纪念勋章" class="nexus-username-medal preview" style="max-height: 11px;max-width: 11px;margin-left: 2pt"><img src="https://img.hdfans.org/images/2024/04/30/HDFans.fw.png" title="HDFans四周年纪念勋章" class="nexus-username-medal preview" style="max-height: 11px;max-width: 11px;margin-left: 2pt"></span>                [<a href="logout.php">退出</a>]
                [<a href="usercp.php">&nbsp;控制面板&nbsp;</a>]
                                                [<a href="torrents.php?inclbookmarked=1&amp;allsec=1&amp;incldead=0">收藏</a>]
                <font class="color_bonus">魔力值 </font>[<a href="mybonus.php">使用</a>]: 3,823,946.2                 <a href="attendance.php" class="faqlink">[签到得魔力]</a>                <a href="medal.php">[勋章]</a>
                <a href="task.php">[任务]</a>
                <font class="color_invite">邀请 </font>[<a href="invite.php?id=13574">发送</a>]: 6(0)                                <br>
	            <font class="color_ratio">分享率:</font> 11.482                <font class="color_uploaded">上传量:</font> 10.597 TB                <font class="color_downloaded"> 下载量:</font> 945.07 GB                <font class="color_active">当前活动:</font> <img class="arrowup" alt="Torrents seeding" title="当前做种" src="pic/trans.gif">4  <img class="arrowdown" alt="Torrents leeching" title="当前下载" src="pic/trans.gif">1&nbsp;&nbsp;
                <font class="color_connectable">可连接:</font><a href="faq.php#id21"><b><font color="red">否</font></b></a> <font class="color_slots">连接数：</font>无限制                <font class="color_bonus">H&amp;R: </font> [<a href="myhr.php">种子区: 0/<font color="red">0</font>/10 特别区: 0/<font color="red">0</font>/10</a>]                <font class="color_bonus">认领: </font> [<a href="claim.php?uid=13574">0/1000</a>]            </span>
        </td>
                        <td class="bottom" align="left" style="border: none">
            <form action="search.php" method="get" target="_blank">
                <div style="display: flex;align-items: center">
                    <div style="display: flex;flex-direction: column">
                        <div>
                            <span><input type="text" name="search" style="width: 80px;height: 12px" value="" placeholder="关键字"></span>
                        </div>
                        <div>
                            <span><select name="search_area" style="width: 88px"><option value="0">标题</option><option value="1">简介</option><option value="3">发布者</option><option value="4">IMDB链接</option></select></span>
                        </div>
                    </div>
                    <div><input type="submit" value="全站搜索" style="width: 39px;white-space: break-spaces;padding: 0"></div>
                </div>
            </form>
        </td>
                	<td class="bottom" align="right"><span class="medium">
 <a href="friends.php"><img class="buddylist" alt="Buddylist" title="社交名单" src="pic/trans.gif"></a> <a href="getrss.php"><img class="rss" alt="RSS" title="获取RSS" src="pic/trans.gif"></a><br><a href="messages.php"><img class="inbox" src="pic/trans.gif" alt="inbox" title="收件箱&nbsp;(无新短讯)"></a> 107 (0 新)  <a href="messages.php?action=viewmailbox&amp;box=-1"><img class="sentbox" alt="sentbox" title="发件箱" src="pic/trans.gif"></a> 3
	</span></td>
	</tr></tbody></table></td>
</tr></tbody></table>
"""

html_txt_2 = """
<table id="info_block" cellpadding="4" cellspacing="0" border="0" width="100%"><tbody><tr>
	<td><table width="100%" cellspacing="0" cellpadding="0" border="0"><tbody><tr>
                                <td class="bottom" align="left"><span class="medium">欢迎回来, <span class="nowrap"><a href="userdetails.php?id=51874" target="_blank" class="PowerUser_Name"><b>XiaoDai</b></a></span><img src="/pic/badge/ann8st-s.png" width="15" height="15" title="八周年（小）"><img src="/pic/badge/ann7st-s.png" width="15" height="15" title="七周年（小）"> [<a onclick="return confirm('Logout?\n退出登陆？');" href="logout.php?token=2ppuS9ZNkN5we7MZ525zKVTUBaT2uGMSeTbLA5Af3TAft64X">退出</a>]    [<a href="torrents.php?inclbookmarked=1&amp;allsec=1&amp;incldead=0">收藏</a>] [<a href="myrss.php">RSS 下载筐</a>] [<a href="badges.php">徽章</a>] [<a href="lottery.php">抽奖</a>]  <span class="color_bonus">魔力值 </span>[<a href="mybonus.php">使用</a>]: 321,401.9         <a href="attendance.php" class="faqlink">签到得魔力</a> <span class="color_invite">邀请 </span>[<a href="invite.php?id=51874">发送</a>]: 0/0<br>
                <span class="color_ratio">分享率：</span> 11.331  <font class="color_uploaded">上传量：</font> 3.482 TB<font class="color_downloaded"> 下载量：</font> 314.71 GB  <font class="color_active">当前活动：</font> <img class="arrowup" alt="Torrents seeding" title="当前做种" src="pic/trans.gif">5  <img class="arrowdown" alt="Torrents leeching" title="当前下载" src="pic/trans.gif">0&nbsp;&nbsp;<font class="color_connectable">H&amp;R: </font>0/10&nbsp;&nbsp;<font class="color_connectable">可连接：</font><b><span style="color: green">是</span></b> &nbsp;<b><a href="blackjack.php">blackjack</a></b>&nbsp;&nbsp;<a href="log.php">&nbsp;日&nbsp;&nbsp;志&nbsp;</a></span></td>

	<td class="bottom" align="right"><span class="medium"><a href="javascript:changelang(25);"><img src="pic/flag/china.gif" width="16" height="10" title="简体中文(Simplified Chinese)" border="0" alt="简体中文(Simplified Chinese)"></a>&nbsp;&nbsp;<a href="javascript:changelang(28);"><img src="pic/flag/hongkong.gif" width="16" height="10" title="繁體中文(Traditional Chinese)" border="0" alt="繁體中文(Traditional Chinese)"></a>&nbsp;&nbsp;<a href="javascript:changelang(6);"><img src="pic/flag/uk.gif" width="16" height="10" title="英文(English)" border="0" alt="英文(English)"></a>&nbsp;&nbsp;当前时间：19:57<br>

<a href="messages.php"><img class="inbox" src="pic/trans.gif" alt="inbox" title="收件箱&nbsp;(无新短讯)"></a> 32 (0 新)  <a href="messages.php?action=viewmailbox&amp;box=-1"><img class="sentbox" alt="sentbox" title="发件箱" src="pic/trans.gif"></a> 0 <a href="friends.php"><img class="buddylist" alt="Buddylist" title="社交名单" src="pic/trans.gif"></a> <a href="getrss.php"><img class="rss" alt="RSS" title="获取RSS" src="pic/trans.gif"></a>
	</span></td>
	</tr></tbody></table></td>
</tr></tbody></table>
"""

html_txt_3 = """
<table id="info_block" cellpadding="4" cellspacing="0" border="0" width="100%">
                <tbody><tr>
                    <td>
                        <table width="100%" cellspacing="0" cellpadding="0" border="0">
                            <tbody><tr>
                                <td class="bottom" align="left">
                                    <font class="medium">欢迎回来</font>,
                                    <span class="nowrap"><a href="userdetails.php?id=15750" class="Rainbow_Name"><b>XiaoDai</b></a><span class="medalcontainer">
        <a href="javascript:;" data-original="https://audiences.me/pic/birthday3.gif">
            <img src="https://audiences.me/pic/birthday3.gif" title="3周年纪念勋章动图版" alt="3周年纪念勋章动图版" style="margin-left: 2pt; max-width: 16px; max-height: 16px;">
        </a></span></span> (UID:15750)                                    [<a href="usercp.php">控制面板</a>]
                                                                                                            [<a href="torrents.php?inclbookmarked=1&amp;allsec=1&amp;incldead=0">收藏</a>]
                                    [<a href="myrss.php">RSS下载筐</a>]
                                    [<a href="mybonus.php">爆米花系统</a>] :
                                    7,725.5                                    <span class="color_bonus">做种积分：</span>2,245,343.0                                    &nbsp;(签到已得400)                                    [<a href="medal_center.php">勋章中心</a>]
                                    <a href="/blackjack.php">[21点]</a>
                                    [<a href="invite.php?id=15750">邀请系统</a>]: 0/0                                    <br>
                                    <span class="color_ratio">分享率：</span> 6.793                                    <font class="color_uploaded">上传量：</font> 11.766 TB                                    <font class="color_downloaded"> 下载量：</font> 1.732 TB                                    <font class="color_active">H&amp;R：</font><a href="myhr.php">  0/<font style="color: red"> 0 </font></a>
                                    <a href="/peerlist.php?userid=15750"><font class="color_active">当前活动：</font></a>
                                    <img class="arrowup" alt="Torrents seeding" title="当前做种" src="pic/trans.gif">145                                    <img class="arrowdown" alt="Torrents leeching" title="当前下载" src="pic/trans.gif">1&nbsp;&nbsp;
<!--                                    <font class='color_connectable'>--><!--</font>-->                                    <font class="color_slots">连接数：</font>无限制                                    &nbsp;&nbsp; <font class="color_active">流量排名：</font>
                                    <img class="arrowup" alt="upload top" title="上传量排名" src="pic/trans.gif"> 4395                                    / <img class="arrowdown" alt="download top" title="下载量排名" src="pic/trans.gif"> 2460&nbsp;&nbsp;
                                    

                                </td>

                                <td class="bottom" align="right"><span class="medium">当前时间：20:01 [<a href="logout.php">退出</a>]<br>

<a href="messages.php"><img class="inbox" src="pic/trans.gif" alt="inbox" title="收件箱&nbsp;(无新短讯)"></a> 20 (0 新)  <a href="messages.php?action=viewmailbox&amp;box=-1"><img class="sentbox" alt="sentbox" title="发件箱" src="pic/trans.gif"></a> 0 <a href="friends.php"><img class="buddylist" alt="Buddylist" title="社交名单" src="pic/trans.gif"></a> <a href="getrss.php"><img class="rss" alt="RSS" title="获取RSS" src="pic/trans.gif"></a>
</span></td>
                            </tr>
                        </tbody></table>
                    </td>
                </tr>
            </tbody></table>
"""

html_txt_4 = """
<table id="info_block" cellpadding="4" cellspacing="0" border="0" width="100%"><tbody><tr>
	<td><table width="100%" cellspacing="0" cellpadding="0" border="0"><tbody><tr style="line-height:2em;">
		<td class="bottom" align="left" style="display:inline-flex;align-items:center;">
			<img src="pic/default_avatar.png" class="leaves-avatar">
            <span class="medium leaves-nav">
                欢迎回来, <span class="nowrap" style="display:inline-flex;align-items:center;"><a href="https://leaves.red/userdetails.php?id=2545" class="EliteUser_Name"><b>XiaoDai<i class="icon-maple" onmouseover="domTT_activate(this, event, 'content', 'UID:<b></b>2545<br>综合排名: <b style=\'color:orangered;\'>2067</b> (<font color=maroon>超过 50%</font>)<br>发种数:<b>0</b> (6505/6505)<br>做种量: <b>523.87 GB</b> (3077/6505)<br>上传量: <b>5.020 TB</b> (2073/6505)<br>时魔: <b>337.764</b> (988/6505)<br>数据更新: 2025-03-06 18:02', 'trail', true, 'delay', 0,'styleClass','niceTitle','maxWidth', 600);"></i></b></a><img src="https://s3.leaves.red/c33abb6ba76a441c9f0683b1723b90a7:red/2023/04/20/644073ed1d477.png" data-preview="https://s3.leaves.red/c33abb6ba76a441c9f0683b1723b90a7:red/2023/04/20/644086bb06b98.webp" title="红叶印象·岸" class="nexus-username-medal preview" style="max-height: 16px;max-width: 16px;margin-left: 2pt"><img src="https://s3.leaves.red/c33abb6ba76a441c9f0683b1723b90a7:red/2024/02/06/65c1b29d36014.webp" data-preview="https://s3.leaves.red/c33abb6ba76a441c9f0683b1723b90a7:red/2024/02/06/65c1b29fb65a8.webp" title="龙年大运" class="nexus-username-medal preview" style="max-height: 16px;max-width: 16px;margin-left: 2pt"><img src="https://s3.leaves.red/c33abb6ba76a441c9f0683b1723b90a7:red/2024/02/06/65c1b4e558af7.png" data-preview="https://s3.leaves.red/c33abb6ba76a441c9f0683b1723b90a7:red/2024/02/06/65c1b4e558af7.png" title="龙年大吉" class="nexus-username-medal preview" style="max-height: 16px;max-width: 16px;margin-left: 2pt"></span>                <a href="logout.php" class="info-item">退出</a>
				<font class="color_ratio">分享率:</font> 19.580                <font class="color_uploaded">上传量:</font> 5.020 TB                <font class="color_downloaded"> 下载量:</font> 262.54 GB                <font class="color_active">当前活动:</font> <img class="arrowup" alt="Torrents seeding" title="当前做种" src="pic/trans.gif">59  <img class="arrowdown" alt="Torrents leeching" title="当前下载" src="pic/trans.gif">0&nbsp;&nbsp;
                <font class="color_connectable"></font>(<b><font color="green">是</font></b>) <font class="color_slots">连接数：</font>无限制                                <br>
				<a href="usercp.php" class="info-item">&nbsp;控制面板&nbsp;</a>
                <a href="torrents.php?inclbookmarked=1&amp;allsec=1&amp;incldead=0" class="info-item">收藏</a>
                <a href="mybonus.php" class="info-item">魔力值 : 881,453.4</a>
				<a href="task.php" class="info-item">任务</a>
				<a href="claim.php?uid=2545" class="info-item">认领:  0/5000</a>                 <a href="attendance_new.php" class="faqlink info-item">立即签到</a>                <!-- <a href="medal.php" style="color:crimson;">[勋章]</a> -->
                <a href="invite.php?id=2545" class="info-item">邀请 : 0(0)</a>
				                                

            </span>
        </td>
                        <td class="bottom" align="left" style="border: none">
            <form action="search.php" method="get" target="_blank">
                <div style="display: flex;align-items: center" class="leaves-nav-search">
                    <div class="search-area">
                        <div>
                            <span><input type="text" name="search" style="width: 100%;height: 12px" value="" placeholder="关键字"></span>
                        </div>
                        <div>
                            <span><select name="search_area" style="width: 88px; visibility: visible;"><option value="0">标题</option><option value="1">简介</option><option value="3">发布者</option><option value="4">IMDB链接</option></select></span>
                        </div>
                    </div>
                    <div><input type="submit" value=""></div>
                </div>
            </form>
        </td>
                	<td class="bottom" align="right"><span class="medium">
 <a href="friends.php"><img class="buddylist" alt="Buddylist" title="社交名单" src="pic/trans.gif"></a> <a href="getrss.php"><img class="rss" alt="RSS" title="获取RSS" src="pic/trans.gif"></a><br><a href="messages.php"><img class="inbox" src="pic/trans.gif" alt="inbox" title="收件箱&nbsp;(无新短讯)"></a> 9 (0 新)  <a href="messages.php?action=viewmailbox&amp;box=-1"><img class="sentbox" alt="sentbox" title="发件箱" src="pic/trans.gif"></a> 0
	</span></td>
	</tr></tbody></table></td>
</tr></tbody></table>
"""






if __name__ == '__main__':
    parser = NexusPHPParser()
    
    print("用户1信息:")
    result1 = parser.get_user_info(html_txt)
    print_user_info(result1)
    
    print("\n用户2信息:")
    result2 = parser.get_user_info(html_txt_1)
    print_user_info(result2)
    
    print("\n用户3信息:")
    result3 = parser.get_user_info(html_txt_2)
    print_user_info(result3)
    
    print("\n用户4信息:")
    result4 = parser.get_user_info(html_txt_3)
    print_user_info(result4)
    
    print("\n用户5信息:")
    result5 = parser.get_user_info(html_txt_4)
    print_user_info(result5)

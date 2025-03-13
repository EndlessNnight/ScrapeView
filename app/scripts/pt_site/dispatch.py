from .sites.pter import PTerSite
from .sites.hdfans import HDFansSite
from .sites.audiences import AudiencesSite
from .sites.hspt import HSptSite
from .sites.mteam import MTeamSite
from .sites.hhanclub import HHAnClubSite
from .sites.raingfh import RaingfhSite
from .sites.rousi import RousiSite
from .sites.nicept import NicePT
from .sites.crabpt import CrabptSite
from .sites.qingwapt import QingwaptSite
# 使用字典映射来替代多个 if-elif 语句
SITE_MAPPING = {
    "pter": {"class": PTerSite, "name": "PTer", "set_params": ["cookie"]},
    "hdfans": {"class": HDFansSite, "name": "HDFans", "set_params": ["cookie"]},
    "audiences": {"class": AudiencesSite, "name": "Audiences", "set_params": ["cookie"]},
    "hspt": {"class": HSptSite, "name": "HSpt", "set_params": ["cookie"]},
    "mteam": {"class": MTeamSite, "name": "M-Team", "set_params": ["api_key", "auth_token"]},
    "hhanclub": {"class": HHAnClubSite, "name": "HHAnClub", "set_params": ["cookie"]},
    "raingfh": {"class": RaingfhSite, "name": "Raingfh", "set_params": ["cookie"]},
    "rousi": {"class": RousiSite, "name": "Rousi", "set_params": ["cookie"]},
    "nicept": {"class": NicePT, "name": "NicePT", "set_params": ["cookie"]},
    "crabpt": {"class": CrabptSite, "name": "蟹黄堡", "set_params": ["cookie"]},
    "qingwapt": {"class": QingwaptSite, "name": "青蛙", "set_params": ["cookie"]}
}

def get_all_sites() -> list[dict[str, str]]:
    """获取所有站点"""
    
    # 返回站点名称和类型
    result = []
    for site_type, site_info in SITE_MAPPING.items():
        result.append({"name": site_info["name"], "type": site_type})
    return result

def dispatch(site_type: str, api_key: str = None, auth_token: str = None, cookie: str = None, user_agent: str = None):
    """
    获取站点实例
    
    Args:
        site_type: 站点类型
        
    Returns:
        站点实例
        
    Raises:
        ValueError: 当站点类型不存在时抛出
    """
    site_class = SITE_MAPPING.get(site_type)
    if not site_class:
        raise ValueError(f"站点 {site_type} 不存在")
    
    pter = site_class["class"]()
    # 获取站点设置参数
    set_params = get_site_set_params(site_type)
    for param in set_params:
        if param == "api_key":
            if api_key:
                pter.set_api_key(api_key)
            else:
                raise ValueError(f"参数 {param} 不能为空")
        elif param == "auth_token":
            if auth_token:
                pter.set_auth_token(auth_token) 
            else:
                raise ValueError(f"参数 {param} 不能为空")
        elif param == "cookie":
            if cookie:
                pter.set_cookies(cookie)
            else:
                raise ValueError(f"参数 {param} 不能为空")
        elif param == "user_agent":
            if user_agent:
                pter.set_headers({"User-Agent": user_agent})
            else:
                raise ValueError(f"参数 {param} 不能为空")
        else:
            raise ValueError(f"不支持的参数: {param}")
    return pter

def get_site_name(site_type: str) -> str:
    """
    获取站点名称
    """
    site_class = SITE_MAPPING.get(site_type)
    if not site_class:
        raise ValueError(f"站点 {site_type} 不存在")
    return site_class["name"]

def get_site_set_params(site_type: str):
    """
    获取站点设置参数
    """
    return SITE_MAPPING.get(site_type)["set_params"]

def get_site_class(site_type: str):
    """
    获取站点类
    """
    return SITE_MAPPING.get(site_type)["class"]



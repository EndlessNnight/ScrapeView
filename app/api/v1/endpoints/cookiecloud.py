from fastapi import APIRouter, HTTPException, Depends, Query, Path, status, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.schemas.common import ApiResponse
from typing import List, Dict, Any
import logging
import traceback
import json
import hashlib
import requests
from base64 import b64decode
from requests.exceptions import RequestException
from app.crud.pt_site import get_site_by_schema_type, create_site, update_site
from app.scripts.pt_site.dispatch import dispatch, get_all_sites, get_site_name, get_site_set_params
from app.scripts.pt_site.dispatch import SITE_MAPPING
from app.schemas.pt_site import SiteCreate

try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import unpad
    from Cryptodome.Protocol.KDF import PBKDF2
except ImportError:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    from Crypto.Protocol.KDF import PBKDF2

logger = logging.getLogger(__name__)

router = APIRouter()

# 域名到站点类型的映射
DOMAIN_TO_SITE_TYPE = {
    "pterclub.com": "pter",
    "hdfans.org": "hdfans",
    "audiences.me": "audiences",
    "hspt.club": "hspt",
    "hhanclub.top": "hhanclub",
    "raingfh.top": "raingfh",
    "nicept.net": "nicept",
    "crabpt.vip": "crabpt",
    "qingwapt.com": "qingwapt",
    "hdsky.me": "hdsky",
    "hdhome.org": "hdhome",
    "azusa.ru": "azusa",
    "kamept.com": "kamept",
    "sunnypt.top": "sunnypt",
    "cspt.top": "cspt",
    "btschool.club": "btschool",
    # 添加更多映射...
}

def decrypt_cookie(server_url, uuid, password):
    """解密COOKIECLOUD数据"""
    try:
        url = f"{server_url}/get/{uuid}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        key = hashlib.md5(f"{uuid}-{password}".encode()).hexdigest()[:16].encode()

        # 解密数据
        try:
            # 解析加密文本
            ciphertext = data['encrypted']

            # 分离salt和IV (CryptoJS格式)
            encrypted = b64decode(ciphertext)
            salt = encrypted[8:16]
            ct = encrypted[16:]
            
            # 使用OpenSSL EVP_BytesToKey导出方式
            key_iv = b""
            prev = b""
            while len(key_iv) < 48:
                prev = hashlib.md5(prev + key + salt).digest()
                key_iv += prev

            _key = key_iv[:32]
            _iv = key_iv[32:48]

            # 创建cipher并解密
            cipher = AES.new(_key, AES.MODE_CBC, _iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)

            # 解析JSON
            return json.loads(pt.decode('utf-8'))

        except Exception as e:
            logger.error(f"数据格式错误: {e}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求错误: {e}")
        return None
    except Exception as e:
        logger.error(f"解密错误: {e}")
        return None
    
@router.post("/decrypt", response_model=ApiResponse[Dict[str, Any]])
async def decrypt_cookiecloud(
    url: str = Body(..., description="URL"),
    uuid: str = Body(..., description="UUID"),
    password: str = Body(..., description="密码"),
    current_user = Depends(get_current_user)
):
    """解密COOKIECLOUD数据"""
    try:
        logger.info(f"开始解密COOKIECLOUD数据: {url}")
        
        # 使用自定义方法解密数据
        decrypted_data = decrypt_cookie(url, uuid, password)
        
        if not decrypted_data:
            logger.error("解密数据失败")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="解密数据失败"
            )
        
        # 检查是否有cookie_data字段,如果存在则处理,没有则抛出异常
        if not isinstance(decrypted_data, dict) or 'cookie_data' not in decrypted_data:
            logger.error("解密数据格式不符合预期")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="解密数据格式不符合预期"
            )
        
        formatted_cookies_by_domain = {}
        
        if isinstance(decrypted_data, dict) and 'cookie_data' in decrypted_data:
            cookie_data = decrypted_data['cookie_data']
            
            # 处理cookie_data
            formatted_cookies_by_domain = {}
            if isinstance(cookie_data, dict):
                for domain, cookies in cookie_data.items():
                    formatted_cookies = []
                    if isinstance(cookies, list):
                        for cookie in cookies:
                            if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                                formatted_cookies.append(f"{cookie['name']}={cookie['value']}")
                    formatted_cookies_by_domain[domain] = '; '.join(formatted_cookies)
            
            return ApiResponse(
                code=200,
                message=f"解密成功",
                data=formatted_cookies_by_domain
            )
    except Exception as e:
        logger.error(f"解密COOKIECLOUD数据失败: {str(e)}")
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解密COOKIECLOUD数据失败: {str(e)}"
        ) 

@router.post("/sync", response_model=ApiResponse[Dict[str, Any]])
async def sync_cookiecloud(
    url: str = Body(..., description="URL"),
    uuid: str = Body(..., description="UUID"),
    password: str = Body(..., description="密码"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """同步COOKIECLOUD站点"""
    try:
        logger.info(f"开始同步COOKIECLOUD站点: {url}")
        
        # 使用自定义方法解密数据
        decrypted_data = decrypt_cookie(url, uuid, password)
        
        if not decrypted_data:
            logger.error("解密数据失败")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="解密数据失败"
            )
        
        # 检查是否有cookie_data字段
        if not isinstance(decrypted_data, dict) or 'cookie_data' not in decrypted_data:
            logger.error("解密数据格式不符合预期")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="解密数据格式不符合预期"
            )
        
        cookie_data = decrypted_data['cookie_data']
        
        # 同步结果
        result = {
            "success_count": 0,
            "failed_count": 0,
            "details": []
        }
        
        # 先格式化所有cookie
        formatted_cookies_by_domain = {}
        if isinstance(cookie_data, dict):
            for domain, cookies in cookie_data.items():
                formatted_cookies = []
                if isinstance(cookies, list):
                    for cookie in cookies:
                        if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                            formatted_cookies.append(f"{cookie['name']}={cookie['value']}")
                formatted_cookies_by_domain[domain] = '; '.join(formatted_cookies)
        
        # 处理格式化后的cookie
        for domain, cookie_string in formatted_cookies_by_domain.items():
            site_type = None
            
            # 检查域名是否在映射中
            for key, value in DOMAIN_TO_SITE_TYPE.items():
                if key in domain:
                    site_type = value
                    break
            
            # 如果找到站点类型，并且站点只需要cookie
            if site_type and site_type in SITE_MAPPING and "cookie" in SITE_MAPPING[site_type].get("set_params", []):
                try:
                    # 检查站点是否已存在
                    existing_site = get_site_by_schema_type(db, site_type, current_user.id)
                    
                    if not existing_site:
                        # 创建站点
                        site_name = SITE_MAPPING[site_type]["name"]
                        
                        # 创建SiteCreate对象
                        site_create = SiteCreate(
                            schema_type=site_type,
                            cookie=cookie_string
                        )
                        
                        try:
                            # 创建PTer实例并获取用户信息
                            pter = dispatch(
                                site_type, 
                                cookie=cookie_string, 
                                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0", 
                                api_key=None, 
                                auth_token=None, 
                                passkey=None
                            )
                            
                            # 获取用户信息
                            user_info = pter.get_user_info()
                            
                            # 如果没有获取到用户信息，则不创建站点
                            if not user_info:
                                raise Exception("无法获取用户信息，请检查cookie是否有效")
                            
                            # 创建站点
                            db_site = create_site(db, site_create, user_id=current_user.id, site_name=site_name)
                            
                            # 创建站点用户关联
                            from app.crud.pt_site import create_site_user
                            create_site_user(db, db_site.id, user_info)
                            
                            result["details"].append({
                                "domain": domain,
                                "site_type": site_type,
                                "status": "created",
                                "username": user_info.username
                            })
                            
                            # 成功创建站点，增加成功计数
                            result["success_count"] += 1
                        except Exception as e:
                            logger.error(f"创建站点失败: {str(e)}")
                            result["failed_count"] += 1
                            result["details"].append({
                                "domain": domain,
                                "site_type": site_type,
                                "status": "failed",
                                "error": str(e)
                            })
                            # 跳过当前站点，继续处理下一个
                            continue
                except Exception as e:
                    logger.error(f"同步站点失败: {str(e)}")
                    result["failed_count"] += 1
                    result["details"].append({
                        "domain": domain,
                        "site_type": site_type,
                        "status": "failed",
                        "error": str(e)
                    })
        
        return ApiResponse(
            code=200,
            message=f"同步成功，成功 {result['success_count']} 个站点，失败 {result['failed_count']} 个站点",
            data=result
        )
    except Exception as e:
        logger.error(f"同步COOKIECLOUD站点失败: {str(e)}")
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步COOKIECLOUD站点失败: {str(e)}"
        ) 

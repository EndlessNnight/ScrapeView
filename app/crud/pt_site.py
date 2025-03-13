from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.pt_site import Site, PTUser, ProxyImage
from app.schemas.pt_site import SiteCreate, SiteUpdate, PTUserCreate, PTUserUpdate, ProxyImageCreate, ProxyImageUpdate
from app.scripts.pt_site.schemas import PTUserInfo
# 获取所有站点
def get_sites(db: Session, user_id: int, skip: int = 0, limit: int = 100, include_user: bool = False) -> List[Site]:
    """获取指定用户的所有站点，可选择是否包含用户信息"""
    query = db.query(Site).filter(Site.user_id == user_id).order_by(Site.created_at.desc())
    if include_user:
        query = query.options(joinedload(Site.user))
    return query.offset(skip).limit(limit).all()

# 获取站点总数
def get_sites_count(db: Session, user_id: int) -> int:
    """获取指定用户的站点总数"""
    return db.query(Site).filter(Site.user_id == user_id).count()

# 根据ID获取站点
def get_site_by_id(db: Session, site_id: int, user_id: int = None, include_user: bool = False) -> Optional[Site]:
    """根据ID获取站点，可选择是否包含用户信息，可选择是否限制用户ID"""
    query = db.query(Site).filter(Site.id == site_id)
    if user_id is not None:
        query = query.filter(Site.user_id == user_id)
    if include_user:
        query = query.options(joinedload(Site.user))
    return query.first()

# 根据URL获取站点
def get_site_by_url(db: Session, url: str, user_id: int = None, include_user: bool = False) -> Optional[Site]:
    """根据URL获取站点，可选择是否包含用户信息，可选择是否限制用户ID"""
    query = db.query(Site).filter(Site.url == url)
    if user_id is not None:
        query = query.filter(Site.user_id == user_id)
    if include_user:
        query = query.options(joinedload(Site.user))
    return query.first()

# 创建站点
def create_site(db: Session, site: SiteCreate, user_id: int = None, site_name: str = None) -> Site:
    """创建站点，可以从参数传入用户ID，也可以从site对象获取"""
    # 构建站点数据
    site_data = {
        "schema_type": site.schema_type,
        "cookie": site.cookie,
        "user_agent": site.user_agent,
        "api_key": site.api_key,
        "auth_token": site.auth_token,
        "user_id": user_id if user_id is not None else site.user_id
    }
    
    # 如果提供了站点名称，添加到数据中
    if site_name:
        site_data["name"] = site_name
    
    # 确保有用户ID
    if site_data["user_id"] is None:
        raise ValueError("创建站点时必须提供用户ID")
    
    # 创建站点对象
    db_site = Site(**site_data)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site

# 更新站点
def update_site(db: Session, site_id: int, site_update: SiteUpdate, user_id: int = None) -> Optional[Site]:
    """更新站点信息"""
    query = db.query(Site).filter(Site.id == site_id)
    
    # 如果提供了用户ID，需要确保是该用户的站点
    if user_id is not None:
        query = query.filter(Site.user_id == user_id)
    
    db_site = query.first()
    if not db_site:
        return None
    
    # 更新数据
    update_data = site_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "url" and value is not None:
            setattr(db_site, key, str(value))  # 将 HttpUrl 转换为字符串
        else:
            setattr(db_site, key, value)
    
    db.commit()
    db.refresh(db_site)
    return db_site

# 删除站点
def delete_site(db: Session, site_id: int) -> bool:
    """删除站点"""
    db_site = get_site_by_id(db, site_id)
    if not db_site:
        return False
    
    db.delete(db_site)
    db.commit()
    return True

# 搜索站点
def search_sites(db: Session, query: str, user_id: int, skip: int = 0, limit: int = 100, include_user: bool = False) -> List[Site]:
    """搜索指定用户的站点，可选择是否包含用户信息"""
    search = f"%{query}%"
    query_obj = db.query(Site).filter(
        Site.user_id == user_id,
        or_(
            Site.url.like(search),
            Site.schema_type.like(search)
        )
    )
    if include_user:
        query_obj = query_obj.options(joinedload(Site.user))
    return query_obj.offset(skip).limit(limit).all()

# 获取站点及其用户
def get_site_with_users(db: Session, site_id: int, user_id: int = None) -> Optional[Site]:
    """获取站点及其PT用户和关联用户，可选择是否限制用户ID"""
    query = db.query(Site).options(
        joinedload(Site.pt_users),
        joinedload(Site.user)
    ).filter(Site.id == site_id)
    
    if user_id is not None:
        query = query.filter(Site.user_id == user_id)
        
    return query.first()

# 获取站点的所有用户
def get_site_users(db: Session, site_id: int) -> List[PTUser]:
    """获取站点的所有PT用户"""
    return db.query(PTUser).filter(PTUser.site_id == site_id).all()

# 创建站点用户
def create_site_user(db: Session, site_id: int, user_info: PTUserInfo) -> PTUser:
    """创建站点用户"""
    db_user = PTUser(
        site_id=site_id,
        username=user_info.username,
        bonus=user_info.bonus,
        ratio=user_info.ratio,
        uploaded=user_info.uploaded,
        downloaded=user_info.downloaded,
        current_upload=user_info.seeding,
        current_download=user_info.leeching
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 更新站点用户
def update_site_user(db: Session, user_id: int, user_data: Union[PTUserUpdate, PTUserInfo]) -> Optional[PTUser]:
    """更新站点用户"""
    db_user = db.query(PTUser).filter(PTUser.id == user_id).first()
    if not db_user:
        return None
    
    # 如果是 PTUserInfo 类型，转换为字典
    if isinstance(user_data, PTUserInfo):
        update_data = {
            "username": user_data.username,
            "bonus": user_data.bonus,
            "ratio": user_data.ratio,
            "uploaded": user_data.uploaded,
            "downloaded": user_data.downloaded,
            "current_upload": 0,  # PTUserInfo 中没有这个字段
            "current_download": 0  # PTUserInfo 中没有这个字段
        }
    else:
        update_data = user_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

# 删除站点用户
def delete_site_user(db: Session, user_id: int) -> bool:
    """删除站点用户"""
    db_user = db.query(PTUser).filter(PTUser.id == user_id).first()
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

# 根据用户ID获取站点
def get_sites_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Site]:
    """根据用户ID获取站点"""
    return db.query(Site).filter(Site.user_id == user_id).offset(skip).limit(limit).all()

# 获取用户的站点数量
def get_user_sites_count(db: Session, user_id: int) -> int:
    """获取用户的站点数量"""
    return db.query(Site).filter(Site.user_id == user_id).count()

# 根据 schema_type 和 user_id 获取站点
def get_site_by_schema_type(db: Session, schema_type: str, user_id: int) -> Optional[Site]:
    """根据架构类型和用户ID获取站点"""
    return db.query(Site).filter(
        Site.schema_type == schema_type,
        Site.user_id == user_id
    ).first()

# ProxyImage CRUD 操作

def get_proxy_image_by_url(db: Session, original_url: str) -> Optional[ProxyImage]:
    """根据原始URL获取代理图片"""
    return db.query(ProxyImage).filter(ProxyImage.original_url == original_url).first()

def get_proxy_image_by_id(db: Session, image_id: int) -> Optional[ProxyImage]:
    """根据ID获取代理图片"""
    return db.query(ProxyImage).filter(ProxyImage.id == image_id).first()

def create_proxy_image(db: Session, image: ProxyImageCreate, local_path: str, file_name: str, 
                      file_size: Optional[int] = None, mime_type: Optional[str] = None) -> ProxyImage:
    """创建代理图片"""
    db_image = ProxyImage(
        original_url=image.original_url,
        local_path=local_path,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def update_proxy_image(db: Session, image_id: int, image_update: ProxyImageUpdate) -> Optional[ProxyImage]:
    """更新代理图片"""
    db_image = get_proxy_image_by_id(db, image_id)
    if not db_image:
        return None
    
    update_data = image_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_image, key, value)
    
    db.commit()
    db.refresh(db_image)
    return db_image

def delete_proxy_image(db: Session, image_id: int) -> bool:
    """删除代理图片"""
    db_image = get_proxy_image_by_id(db, image_id)
    if not db_image:
        return False
    
    db.delete(db_image)
    db.commit()
    return True 
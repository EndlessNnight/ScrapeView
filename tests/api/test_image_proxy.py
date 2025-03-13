import pytest
import os
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.v1.endpoints.pt_site import download_and_store_image
from app.core.config import settings
from app.db.session import get_db

client = TestClient(app)

# 测试URL
TEST_URL = "https://img.pterclub.com/images/2023/12/25/12r5gl0.jpg"

# 覆盖数据库依赖
def override_get_db():
    try:
        db = next(get_db())
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.mark.asyncio
async def test_download_and_store_image():
    """测试使用 download_and_store_image 函数下载图片"""
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 调用函数下载图片
        file_path, content_type, db_image = await download_and_store_image(
            url=TEST_URL,
            db=db
        )
        
        # 验证结果
        assert os.path.exists(file_path), "文件未创建"
        assert os.path.getsize(file_path) > 0, "文件大小为0"
        assert content_type.startswith("image/"), f"内容类型不是图片: {content_type}"
        assert db_image is not None, "数据库记录未创建"
        assert db_image.original_url == TEST_URL, "URL不匹配"
        
        print(f"图片已成功下载到: {file_path}")
        print(f"内容类型: {content_type}")
        print(f"文件大小: {os.path.getsize(file_path)} bytes")
        
    finally:
        # 清理测试数据
        if db_image and db_image.id:
            db.delete(db_image)
            db.commit()
        
        # 删除测试文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

@pytest.mark.asyncio
async def test_proxy_image_endpoint():
    """测试图片代理端点"""
    # 发送请求
    response = client.get(f"/api/v1/ptsites/images/proxy?url={TEST_URL}")
    
    # 验证响应
    assert response.status_code == 200, f"请求失败: {response.status_code}"
    assert response.headers.get("content-type", "").startswith("image/"), "响应不是图片"
    assert len(response.content) > 0, "响应内容为空"
    
    print(f"代理图片成功，内容类型: {response.headers.get('content-type')}")
    print(f"响应大小: {len(response.content)} bytes")

if __name__ == "__main__":
    # 清理测试目录
    test_dir = Path(settings.IMAGES_STORAGE_PATH)
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # 运行测试
    pytest.main(["-xvs", __file__]) 
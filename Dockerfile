FROM python:3.12-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SCRAPEVIEW_DB_TYPE=sqlite \
    SCRAPEVIEW_SQLITE_PATH=/app/db/scrapeview.db \
    SCRAPEVIEW_ENVIRONMENT=production

# 安装依赖 - 尝试多个镜像源
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据库目录
RUN mkdir -p /app/db

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 
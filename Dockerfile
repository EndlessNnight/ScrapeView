FROM python:3.12-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SCRAPEVIEW_DB_TYPE=sqlite \
    SCRAPEVIEW_SQLITE_PATH=/app/db/scrapeview.db \
    SCRAPEVIEW_ENVIRONMENT=production \
    LOG_DIR=/app/logs

# 安装系统依赖
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     python3-dev \
#     default-libmysqlclient-dev \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p /app/db /app/logs /app/uploads/images

# 复制项目文件
COPY . .

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "正在应用数据库迁移..."\n\
alembic upgrade head\n\
echo "数据库迁移完成"\n\
\n\
echo "启动应用服务..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# 设置卷挂载点
VOLUME ["/app/db", "/app/logs", "/app/uploads"]

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# 启动命令
CMD ["/app/start.sh"] 
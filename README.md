# ScrapeView

ScrapeView是一个用于数据采集和展示的Web应用程序，基于FastAPI构建。

## 功能特性

- 数据采集和处理
- PT站点管理和种子搜索
- 图片代理和缓存
- 用户认证和授权
- 任务调度和管理
- API日志记录和查询

## 技术栈

- **后端**: FastAPI, SQLAlchemy, Alembic, Pydantic
- **数据库**: SQLite/MySQL
- **部署**: Docker, Docker Compose

## 快速开始

### 使用Docker

最简单的启动方式是使用Docker Compose:

```bash
# 克隆仓库
git clone https://github.com/yourusername/ScrapeView.git
cd ScrapeView

# 创建环境变量文件
cp .env.example .env
# 编辑.env文件，根据需要修改配置

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 手动安装

如果您想手动安装和运行:

```bash
# 克隆仓库
git clone https://github.com/yourusername/ScrapeView.git
cd ScrapeView

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 创建环境变量文件
cp .env.example .env
# 编辑.env文件，根据需要修改配置

# 应用数据库迁移
alembic upgrade head

# 启动应用
uvicorn app.main:app --reload
```

## 数据库迁移

项目使用Alembic进行数据库迁移管理:

```bash
# 创建新的迁移版本
alembic revision --autogenerate -m "描述你的变更"

# 应用所有迁移
alembic upgrade head

# 回滚到上一个版本
alembic downgrade -1

# 查看迁移历史
alembic history
```

## Docker部署

### 构建镜像

```bash
docker build -t scrapeview:latest .
```

### 运行容器

```bash
docker run -d \
  --name scrapeview \
  -p 8000:8000 \
  -v ./db:/app/db \
  -v ./logs:/app/logs \
  -v ./uploads:/app/uploads \
  scrapeview:latest
```

### 使用Docker Compose

```bash
docker-compose up -d
```

## 项目结构

```
ScrapeView/
├── alembic/                # 数据库迁移
├── app/                    # 应用代码
│   ├── api/                # API路由
│   ├── core/               # 核心功能
│   ├── crud/               # 数据库操作
│   ├── db/                 # 数据库配置
│   ├── models/             # 数据库模型
│   ├── schemas/            # Pydantic模型
│   ├── services/           # 业务逻辑
│   └── main.py             # 应用入口
├── db/                     # 数据库文件
├── logs/                   # 日志文件
├── uploads/                # 上传文件
├── .dockerignore           # Docker忽略文件
├── .env.example            # 环境变量示例
├── .gitignore              # Git忽略文件
├── alembic.ini             # Alembic配置
├── docker-compose.yml      # Docker Compose配置
├── Dockerfile              # Docker构建文件
├── README.md               # 项目说明
└── requirements.txt        # 依赖列表
```

## API文档

启动应用后，可以通过以下URL访问API文档:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 许可证

[MIT License](LICENSE)
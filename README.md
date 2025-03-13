# ScrapeView

ScrapeView是一个基于FastAPI开发的数据采集和展示平台，支持抖音等平台的数据采集、处理和可视化展示。

## 功能特点

- 支持抖音创作者和视频数据采集
- 灵活的数据库配置（MySQL/SQLite）
- 任务调度系统
- RESTful API接口
- 支持开发和生产环境配置

## 技术栈

- **后端框架**: FastAPI
- **数据库**: MySQL/SQLite
- **ORM**: SQLAlchemy
- **数据迁移**: Alembic
- **任务调度**: APScheduler
- **依赖管理**: pip

## 安装指南

### 环境要求

- Python 3.8+
- MySQL (可选，也支持SQLite)

### 安装步骤

1. 克隆仓库

```bash
git clone https://gitea.luckynex.cn:4310/yolo/ScrapeView.git
cd ScrapeView
```

2. 创建虚拟环境

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 配置环境变量

根据需要选择数据库类型，复制对应的环境变量配置文件：

- 使用SQLite (推荐开发环境)：
  ```bash
  cp .env.sqlite .env
  ```

- 使用MySQL：
  ```bash
  cp .env.example .env
  # 然后编辑.env文件，配置MySQL连接信息
  ```

5. 初始化数据库

```bash
# 使用Alembic创建数据库表
alembic upgrade head
```

6. 启动应用

```bash
uvicorn app.main:app --reload
```

应用将在 http://localhost:8000 运行，API文档可在 http://localhost:8000/docs 访问。

## 配置说明

### 数据库配置

ScrapeView支持两种数据库配置方式：

#### SQLite配置 (适合开发环境)

编辑`.env`文件：

```
# 是否使用环境变量配置数据库
SCRAPEVIEW_USE_ENV_CONFIG=true

# 环境设置（development/production）
SCRAPEVIEW_ENVIRONMENT=development

# 数据库类型（mysql/sqlite）
SCRAPEVIEW_DB_TYPE=sqlite

# SQLite数据库配置
# 默认路径为项目根目录下的sqlite.db
SCRAPEVIEW_SQLITE_PATH=sqlite.db
```

#### MySQL配置 (适合生产环境)

编辑`.env`文件：

```
# 是否使用环境变量配置数据库
SCRAPEVIEW_USE_ENV_CONFIG=true

# 环境设置（development/production）
SCRAPEVIEW_ENVIRONMENT=production

# 数据库类型（mysql/sqlite）
SCRAPEVIEW_DB_TYPE=mysql

# MySQL数据库配置
SCRAPEVIEW_DB_HOST=your_mysql_host
SCRAPEVIEW_DB_PORT=3306
SCRAPEVIEW_DB_USER=your_username
SCRAPEVIEW_DB_PASSWORD=your_password
SCRAPEVIEW_DB_NAME=scrape_view
```

### 环境变量说明

| 环境变量 | 说明 | 默认值 |
|---------|------|-------|
| SCRAPEVIEW_USE_ENV_CONFIG | 是否使用环境变量配置 | true |
| SCRAPEVIEW_ENVIRONMENT | 环境设置 (development/production) | development |
| SCRAPEVIEW_DB_TYPE | 数据库类型 (mysql/sqlite) | mysql |
| SCRAPEVIEW_DB_HOST | MySQL主机地址 | localhost |
| SCRAPEVIEW_DB_PORT | MySQL端口 | 3306 |
| SCRAPEVIEW_DB_USER | MySQL用户名 | root |
| SCRAPEVIEW_DB_PASSWORD | MySQL密码 | root |
| SCRAPEVIEW_DB_NAME | MySQL数据库名 | scrape_view_dev |
| SCRAPEVIEW_SQLITE_PATH | SQLite数据库文件路径 | sqlite.db |

## API接口

### 认证接口

- `POST /v1/login`: 用户登录
- `POST /v1/refresh`: 刷新令牌

### 抖音数据接口

- `GET /v1/douyin/creators`: 获取创作者列表
- `POST /v1/douyin/creators`: 添加创作者
- `GET /v1/douyin/creators/{creator_id}`: 获取创作者详情
- `GET /v1/douyin/contents`: 获取内容列表
- `GET /v1/douyin/contents/{content_id}`: 获取内容详情

### 任务接口

- `GET /v1/tasks`: 获取任务列表
- `POST /v1/tasks`: 创建任务
- `GET /v1/tasks/{task_id}`: 获取任务详情

## 开发指南

### 项目结构

```
ScrapeView/
├── alembic/              # 数据库迁移
├── app/
│   ├── api/              # API路由
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/             # 核心配置
│   ├── crud/             # 数据库操作
│   ├── db/               # 数据库连接
│   ├── models/           # 数据库模型
│   ├── schemas/          # Pydantic模型
│   ├── scripts/          # 脚本
│   │   └── douyin/       # 抖音相关脚本
│   ├── services/         # 业务逻辑
│   └── main.py           # 应用入口
├── .env                  # 环境变量
├── .env.example          # 环境变量示例
├── .env.sqlite           # SQLite环境变量示例
├── requirements.txt      # 依赖列表
└── README.md             # 项目说明
```

### 添加新功能

1. 在`app/models`中定义数据库模型
2. 在`app/schemas`中定义Pydantic模型
3. 在`app/crud`中实现数据库操作
4. 在`app/api/v1/endpoints`中实现API接口
5. 在`app/main.py`中注册路由

### 数据库迁移

创建新的迁移：

```bash
alembic revision --autogenerate -m "描述"
```

应用迁移：

```bash
alembic upgrade head
```

## 部署指南

### 使用Docker部署

1. 构建Docker镜像

```bash
docker build -t scrapeview .
```

2. 运行容器

```bash
docker run -d -p 8000:8000 --name scrapeview \
  -e SCRAPEVIEW_ENVIRONMENT=production \
  -e SCRAPEVIEW_DB_TYPE=mysql \
  -e SCRAPEVIEW_DB_HOST=your_mysql_host \
  -e SCRAPEVIEW_DB_PORT=3306 \
  -e SCRAPEVIEW_DB_USER=your_username \
  -e SCRAPEVIEW_DB_PASSWORD=your_password \
  -e SCRAPEVIEW_DB_NAME=scrape_view \
  scrapeview
```

### 使用Nginx和Gunicorn部署

1. 安装Gunicorn

```bash
pip install gunicorn
```

2. 创建Gunicorn配置文件`gunicorn_conf.py`

```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
```

3. 启动Gunicorn

```bash
gunicorn -c gunicorn_conf.py app.main:app
```

4. 配置Nginx

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 常见问题

### 数据库连接失败

- 检查数据库配置是否正确
- 确保数据库服务器正在运行
- 检查防火墙设置

### 任务调度问题

- 检查APScheduler配置
- 查看日志文件了解详细错误信息

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请通过以下方式联系我们：

- 邮箱: your.email@example.com
- GitHub Issues: https://github.com/yourusername/ScrapeView/issues 
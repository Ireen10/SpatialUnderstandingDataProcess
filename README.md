# SpatialUnderstandingDataProcess

空间理解多模态 VLM 训练数据处理平台

## 功能特性

- 🔐 **多用户系统** - 用户注册/登录、JWT认证、权限隔离
- 🔑 **API Key管理** - 配额控制、自定义LLM配置
- 📥 **数据下载** - HuggingFace Hub、自定义URL下载
- 📊 **数据管理** - 文件索引、元数据提取、存储管理
- 👁️ **数据可视化** - 图像/视频预览、配对数据展示、HTML画廊
- 🤖 **AI辅助** - GLM-5集成、可视化代码生成、格式转换脚本
- 📈 **统计分析** - 数据概览、时间线、类型分布
- 🔍 **数据搜索** - 文件名搜索、模糊匹配
- 🐳 **Docker部署** - 一键部署、Celery任务队列

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy |
| 前端 | React 18+ / TypeScript / Vite / Ant Design |
| 数据库 | PostgreSQL (生产) / SQLite (开发) |
| 缓存 | Redis |
| 任务队列 | Celery |
| AI | OpenRouter GLM-5 |
| 部署 | Docker / Docker Compose |

## 快速开始

### 开发环境

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
cp .env.example .env
# 编辑 .env 配置 OPENROUTER_API_KEY
python run.py

# 前端
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
cd docker
docker-compose up -d
```

访问 http://localhost 查看前端，http://localhost:8000/docs 查看API文档。

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/          # API路由
│   │   │   ├── auth.py       # 认证
│   │   │   ├── api_keys.py   # API Key管理
│   │   │   ├── datasets.py   # 数据集管理
│   │   │   ├── tasks.py      # 任务管理
│   │   │   ├── ai.py         # AI辅助功能
│   │   │   ├── files.py      # 文件服务
│   │   │   ├── statistics.py # 统计分析
│   │   │   └── search.py     # 搜索功能
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据库模型
│   │   ├── schemas/      # Pydantic模式
│   │   ├── services/     # 业务逻辑
│   │   └── worker.py     # Celery Worker
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/          # API客户端
│   │   ├── layouts/      # 布局组件
│   │   ├── pages/        # 页面组件
│   │   └── stores/       # 状态管理
│   └── package.json
├── docker/               # Docker配置
└── data/                 # 数据存储
```

## API 文档

启动后端后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发进度

| # | 功能 | 状态 |
|---|------|------|
| 001 | 项目架构设计 | ✅ |
| 002 | 多用户系统与权限隔离 | ✅ |
| 003 | 配置管理系统 | ✅ |
| 004 | 数据下载模块 | ✅ |
| 005 | 任务队列集成 | ✅ |
| 006 | 数据存储与索引 | ✅ |
| 007 | 元数据提取系统 | ✅ |
| 008 | 数据可视化模块 | ✅ |
| 010 | AI辅助功能 | ✅ |
| 013 | 数据统计功能 | ✅ |
| 015 | 任务队列与异步处理 | ✅ |
| 017 | 部署与服务管理 | ✅ |
| 018 | 数据搜索功能 | ✅ |
| 009 | 数据格式转换系统 | 🔄 |
| 011 | 数据Bug标记与AI修复 | 📋 |
| 012 | 数据版本管理 | 📋 |
| 014 | 数据导出功能 | 📋 |
| 016 | 日志与监控系统 | 📋 |
| 019 | 数据备份机制 | 📋 |
| 020 | 数据质量评估预留接口 | 📋 |

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SECRET_KEY | JWT密钥 | - |
| DATABASE_URL | 数据库URL | sqlite+aiosqlite:///./spatial_data.db |
| REDIS_URL | Redis URL | redis://localhost:6379/0 |
| DATA_STORAGE_PATH | 数据存储路径 | ./data |
| OPENROUTER_API_KEY | OpenRouter API Key | - |
| OPENROUTER_MODEL | 模型名称 | z-ai/glm-5 |
| HTTP_PROXY | HTTP代理 | - |

## License

MIT

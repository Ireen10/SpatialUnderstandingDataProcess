# SpatialUnderstandingDataProcess

空间理解多模态 VLM 训练数据处理平台

## 功能特性

### 核心功能
- 🔐 **多用户系统** - 用户注册/登录、JWT认证、权限隔离
- 🔑 **API Key管理** - 配额控制、自定义LLM配置
- 📥 **数据下载** - HuggingFace Hub、自定义URL下载
- 📊 **数据管理** - 文件索引、元数据提取、存储管理

### 数据处理
- 👁️ **数据可视化** - 图像/视频预览、配对数据展示、HTML画廊
- 🤖 **AI辅助** - GLM-5集成、可视化代码生成、格式转换脚本
- 🔄 **格式转换** - JSON/JSONL/CSV、COCO/YOLO标注格式
- 📦 **数据导出** - ZIP/TAR打包、训练格式导出

### 数据治理
- 🔍 **数据搜索** - 文件名搜索、模糊匹配
- 📈 **统计分析** - 数据概览、时间线、类型分布
- 🐛 **Bug标记** - 问题报告、AI修复建议、批量处理
- 💾 **数据备份** - 完整/增量备份、恢复功能
- 📋 **版本管理** - 快照、回滚、差异对比
- 📝 **审计日志** - 操作追踪、系统监控

### 部署运维
- 🐳 **Docker部署** - 一键部署、Celery任务队列
- 🩺 **健康监控** - 系统状态、性能指标

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
| 版本控制 | Git / DVC (可选) |

## 快速开始

### 一键启动

**Windows**：
```bash
start.bat
```

**Linux/Mac**：
```bash
chmod +x start.sh
./start.sh
```

启动后会显示访问地址，例如：
```
访问地址:
  前端:   http://192.168.1.100:5173
  后端:   http://192.168.1.100:8080
  API文档: http://192.168.1.100:8080/docs
```

### 首次使用

1. 访问前端地址（如 http://192.168.1.100:5173）
2. 系统会自动进入**初始化页面**
3. 填写管理员账户信息（用户名、邮箱、密码）
4. 点击"完成注册"
5. 可选：配置 AI 模型、代理、存储后端
6. 开始使用

### 手动安装

**后端**：
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**前端**：
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

## 部署方式

### 方式一：一键部署（生产环境）

**Windows**：
```bash
deploy.bat
```

**Linux/Mac**：
```bash
chmod +x deploy.sh
./deploy.sh
```

部署完成后访问：`http://<你的IP>`

---

### 方式二：Docker Compose（推荐生产环境）

```bash
# 1. 创建环境配置
cp .env.example .env
# 编辑 .env 配置 SECRET_KEY 和 OPENROUTER_API_KEY

# 2. 启动服务
docker compose up -d --build

# 3. 查看日志
docker compose logs -f
```

访问地址：
- 前端：`http://localhost`
- API文档：`http://localhost:8080/docs`

---

### 方式三：开发模式

```bash
cd docker
docker-compose up -d
```

访问 http://localhost 查看前端，http://localhost:8000/docs 查看API文档。

## API 端点汇总

| 模块 | 端点数 | 说明 |
|------|--------|------|
| 认证 | 3 | 注册、登录、用户信息 |
| API Key | 6 | 创建、管理、配额控制 |
| 数据集 | 8 | CRUD、下载、扫描 |
| 任务 | 4 | 列表、详情、取消、重试 |
| AI | 5 | 可视化、转换脚本、质量分析、聊天 |
| 统计 | 3 | 概览、时间线、数据集统计 |
| 搜索 | 2 | 文件搜索、数据集搜索 |
| 转换/导出 | 5 | 格式转换、导出、训练格式 |
| 备份 | 6 | 创建、恢复、删除、清理 |
| Bug | 7 | 报告、状态、AI分析、扫描 |
| 版本 | 5 | 快照、恢复、对比、删除 |
| 监控 | 6 | 审计日志、指标、健康状态 |

**总计：60+ API 端点**

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
| 009 | 数据格式转换系统 | ✅ |
| 010 | AI辅助功能 | ✅ |
| 011 | 数据Bug标记与AI修复 | ✅ |
| 012 | 数据版本管理 | ✅ |
| 013 | 数据统计功能 | ✅ |
| 014 | 数据导出功能 | ✅ |
| 015 | 任务队列与异步处理 | ✅ |
| 016 | 日志与监控系统 | ✅ |
| 017 | 部署与服务管理 | ✅ |
| 018 | 数据搜索功能 | ✅ |
| 019 | 数据备份机制 | ✅ |
| 020 | 数据质量评估 | ✅ |
| 021 | 初始化配置向导 | ✅ |

**完成度: 21/21 (100%) 🎉**

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SECRET_KEY | JWT密钥 | - |
| DATABASE_URL | 数据库URL | sqlite+aiosqlite:///./spatial_v2.db |
| REDIS_URL | Redis URL | redis://localhost:6379/0 |
| DATA_STORAGE_PATH | 数据存储路径 | ./data |
| OPENROUTER_API_KEY | OpenRouter API Key | - |
| OPENROUTER_MODEL | 模型名称 | z-ai/glm-5 |
| HTTP_PROXY | HTTP代理 | - |

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/          # API路由 (12个模块)
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据库模型
│   │   ├── schemas/      # Pydantic模式
│   │   ├── services/     # 业务逻辑 (8个服务)
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

## License

MIT

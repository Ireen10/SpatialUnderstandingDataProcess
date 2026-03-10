# SpatialUnderstandingDataProcess

空间理解多模态 VLM 训练数据处理平台

## 功能特性

### 🎨 流程设计器 v3.0 (新增) ⭐⭐⭐

**核心特性**:
- 🖱️ **可视化拖拽** - 从模块库拖拽到画布，自动连接
- 🔌 **端口化架构** - 统一端口 ID 格式 (`{owner}:{port}:{index}`)
- 🔗 **连线即映射** - 简洁的连接定义，无需额外配置
- ⚙️ **参数配置** - 动态表单，根据类型自动选择控件
- 📥 **输入配置** - 执行前配置流程输入参数
- 📤 **结果展示** - 实时显示执行结果
- 💾 **流程存储** - 保存/加载/删除流程（JSON 格式）
- 📋 **流程列表** - 查看所有已保存流程

**快速开始**:
1. 从左侧模块库拖拽模块到画布
2. 从输出端口拖拽连线到输入端口
3. 点击节点配置参数
4. 点击"保存"保存流程
5. 点击"执行"运行流程

### 核心功能
- 🔐 **双角色权限系统** - 超级用户（全功能）/ 普通用户（仅浏览导出）、禁用公开注册
- 🤖 **AI 辅助** - GLM-5 集成、可视化代码生成、格式转换脚本（仅超级用户）
- 🔑 **LLM 统一配置** - 超级用户配置 Base URL/API-Key/Model，所有 AI 功能共享
- 📥 **数据下载** - HuggingFace Hub、自定义 URL 下载
- 📊 **数据管理** - 文件索引、元数据提取、存储管理

### 数据处理
- 👁️ **数据可视化** - 通用卡片式展示（每页 50 个）、图片自动下载、视频封面提取
- 🔄 **格式转换** - JSON/JSONL/CSV、COCO/YOLO 标注格式
- 📦 **数据导出** - ZIP/TAR 打包、训练格式导出
- 🤖 **AI 自定义可视化** - 特殊需求时 AI 生成 HTML（可选）

### 数据治理
- 🔍 **数据搜索** - 文件名搜索、模糊匹配
- 📈 **统计分析** - 数据概览、时间线、类型分布
- 🐛 **Bug 标记** - 问题报告、AI 修复建议、批量处理（仅超级用户）
- 💾 **数据备份** - 完整/增量备份、恢复功能
- 📋 **版本管理** - 快照、回滚、差异对比
- 📝 **审计日志** - 操作追踪、系统监控

### 部署运维
- 🐳 **Docker 部署** - 一键部署、Celery 任务队列
- 🩺 **健康监控** - 系统状态、性能指标

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy |
| 前端 | React 18+ / TypeScript / Vite / Ant Design |
| 数据库 | PostgreSQL (生产) / SQLite (开发) |
| 缓存 | Redis |
| 任务队列 | Celery |
| AI | OpenRouter GLM-5（仅超级用户配置） |
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
  前端：http://192.168.1.100:5173
  后端：http://192.168.1.100:8080
  API 文档：http://192.168.1.100:8080/docs
```

### 首次使用

1. 访问前端地址（如 http://192.168.1.100:5173）
2. 系统会自动进入**初始化页面**
3. 创建**超级用户**账户（用户名、邮箱、密码）
4. 可选：配置 LLM 服务（Base URL、API Key、Model Name）
5. 可选：配置代理、存储后端
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

部署完成后访问：`http://<你的 IP>`

---

### 方式二：Docker Compose（推荐生产环境）

```bash
# 1. 创建环境配置
cp .env.example .env
# 编辑 .env 配置 SECRET_KEY

# 2. 启动服务
docker compose up -d --build

# 3. 查看日志
docker compose logs -f
```

访问地址：
- 前端：`http://localhost`
- API 文档：`http://localhost:8080/docs`

---

### 方式三：开发模式

```bash
cd docker
docker-compose up -d
```

访问 http://localhost 查看前端，http://localhost:8000/docs 查看 API 文档。

## 用户角色说明

| 功能 | 超级用户 | 普通用户 |
|------|----------|----------|
| 登录 | ✅ | ✅ |
| 浏览数据集 | ✅ | ✅ |
| 导出数据集 | ✅ | ✅ |
| LLM 配置 | ✅ | ❌ |
| AI 生成可视化 | ✅ | ❌ |
| AI 生成转换脚本 | ✅ | ❌ |
| 数据 Bug 标记 | ✅ | ❌ |
| 数据备份/恢复 | ✅ | ❌ |
| 版本管理 | ✅ | ❌ |

**注意**：
- 禁用公开注册，仅支持超级用户手动创建账户
- LLM 配置（Base URL、API Key、Model）仅超级用户可在设置页面配置
- AI 功能入口对普通用户隐藏

## API 端点汇总

| 模块 | 端点数 | 说明 |
|------|--------|------|
| 认证 | 3 | 登录、用户信息（禁用注册） |
| 数据集 | 8 | CRUD、下载、扫描 |
| 任务 | 4 | 列表、详情、取消、重试 |
| AI | 5 | 可视化、转换脚本、质量分析、聊天（仅超级用户） |
| 统计 | 3 | 概览、时间线、数据集统计 |
| 搜索 | 2 | 文件搜索、数据集搜索 |
| 转换/导出 | 5 | 格式转换、导出、训练格式 |
| 备份 | 6 | 创建、恢复、删除、清理 |
| Bug | 7 | 报告、状态、AI 分析、扫描（仅超级用户） |
| 版本 | 5 | 快照、恢复、对比、删除 |
| 监控 | 6 | 审计日志、指标、健康状态 |
| LLM 配置 | 3 | 获取、更新、测试（仅超级用户） |

**总计：60+ API 端点**

## 开发进度

| # | 功能 | 状态 |
|---|------|------|
| 001 | 项目架构设计 | ✅ |
| 002 | 双角色权限系统 | 🔄 |
| 003 | LLM 统一配置管理 | 🔄 |
| 004 | 数据下载模块 | ✅ |
| 005 | 任务队列集成 | ✅ |
| 006 | 数据存储与索引 | ✅ |
| 007 | 元数据提取系统 | ✅ |
| 008 | 数据可视化模块 | ✅ |
| 009 | 数据格式转换系统 | ✅ |
| 010 | AI 辅助功能（权限调整） | 🔄 |
| 011 | 数据 Bug 标记与 AI 修复（权限调整） | 🔄 |
| 012 | 数据版本管理 | ✅ |
| 013 | 数据统计功能 | ✅ |
| 014 | 数据导出功能 | ✅ |
| 015 | 任务队列与异步处理 | ✅ |
| 016 | 日志与监控系统 | ✅ |
| 017 | 部署与服务管理 | ✅ |
| 018 | 数据搜索功能 | ✅ |
| 019 | 数据备份机制 | ✅ |
| 020 | 数据质量评估 | ✅ |
| 021 | 初始化配置向导（LLM 配置调整） | 🔄 |
| 022 | 一键部署与生产环境支持 | ✅ |
| 023 | 通用卡片式可视化（保底方案） | 🔄 |

**完成度：15/23 (65%)**

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SECRET_KEY | JWT 密钥 | - |
| DATABASE_URL | 数据库 URL | sqlite+aiosqlite:///./spatial_v2.db |
| REDIS_URL | Redis URL | redis://localhost:6379/0 |
| DATA_STORAGE_PATH | 数据存储路径 | ./data |
| HTTP_PROXY | HTTP 代理 | - |

**注意**：LLM 配置（OPENROUTER_API_KEY、OPENROUTER_MODEL 等）已迁移至数据库，由超级用户在设置页面配置。

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由 (13 个模块)
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据库模型
│   │   ├── schemas/      # Pydantic 模式
│   │   ├── services/     # 业务逻辑 (9 个服务)
│   │   └── worker.py     # Celery Worker
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── layouts/      # 布局组件
│   │   ├── pages/        # 页面组件
│   │   └── stores/       # 状态管理
│   └── package.json
├── docker/               # Docker 配置
└── data/                 # 数据存储
```

## License

MIT

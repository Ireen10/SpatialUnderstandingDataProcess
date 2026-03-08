# SpatialUnderstandingDataProcess

空间理解多模态 VLM 训练数据处理平台

## 功能特性

- 多用户系统与权限隔离
- API Key 管理与配额控制
- 数据集管理与索引
- HuggingFace 数据集下载
- AI 辅助数据可视化与格式转换
- Docker 容器化部署

## 技术栈

- **后端**: Python 3.10+ / FastAPI / SQLAlchemy
- **前端**: React 18+ / TypeScript / Vite / Ant Design
- **数据库**: PostgreSQL (生产) / SQLite (开发)
- **缓存**: Redis
- **任务队列**: Celery
- **部署**: Docker / Docker Compose

## 快速开始

### 开发环境

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
cp .env.example .env
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

## API 文档

启动后端后访问: http://localhost:8000/docs

## 项目结构

```
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/       # API 路由
│   │   ├── core/      # 核心配置
│   │   ├── models/    # 数据库模型
│   │   └── schemas/   # Pydantic 模式
│   └── pyproject.toml
├── frontend/          # React 前端
│   ├── src/
│   │   ├── api/       # API 客户端
│   │   ├── layouts/   # 布局组件
│   │   ├── pages/     # 页面组件
│   │   └── stores/    # 状态管理
│   └── package.json
├── docker/            # Docker 配置
│   ├── docker-compose.yml
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
└── data/              # 数据存储
```

## 进度

- [x] US-001 项目架构设计与技术选型
- [x] US-002 多用户系统与权限隔离
- [x] US-003 配置管理系统
- [ ] US-004 数据下载模块
- [ ] US-006 数据存储与索引
- [ ] US-007 元数据提取系统
- [ ] US-008 数据可视化模块
- [ ] US-009 数据格式转换系统
- [ ] US-010 AI Coding 辅助

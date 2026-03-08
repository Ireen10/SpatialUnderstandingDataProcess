# SpatialUnderstandingDataProcess 详细设计文档

## 目录

1. [系统架构](#系统架构)
2. [目录结构](#目录结构)
3. [后端模块详解](#后端模块详解)
   - [核心模块 (core)](#核心模块-core)
   - [数据模型 (models)](#数据模型-models)
   - [API路由 (api)](#api路由-api)
   - [业务服务 (services)](#业务服务-services)
4. [前端模块详解](#前端模块详解)
5. [API接口文档](#api接口文档)
6. [数据库设计](#数据库设计)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (React + TypeScript)                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ 登录注册 │ │ 数据管理 │ │ 可视化  │ │ AI助手  │ │ 系统设置 │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
└───────┼──────────┼──────────┼──────────┼──────────┼─────────────┘
        │          │          │          │          │
        └──────────┴──────────┼──────────┴──────────┘
                              │ HTTP/REST API
┌─────────────────────────────┼───────────────────────────────────┐
│                         后端 (FastAPI)                           │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │                    API 路由层                               │  │
│  │  auth │ datasets │ files │ ai │ bugs │ versions │ ...    │  │
│  └───────────────────────────┼───────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │                    业务服务层                               │  │
│  │  download │ conversion │ visualization │ ai │ backup ... │  │
│  └───────────────────────────┼───────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │                    数据访问层                               │  │
│  │              SQLAlchemy ORM + AsyncSession                 │  │
│  └───────────────────────────┼───────────────────────────────┘  │
└──────────────────────────────┼──────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                       数据存储层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   SQLite    │  │    Redis    │  │  文件存储    │             │
│  │   (数据库)   │  │  (缓存/队列) │  │  (本地/S3)  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
SpatialUnderstandingDataProcess/
├── backend/                          # 后端代码
│   ├── app/
│   │   ├── api/                      # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # 认证相关 API
│   │   │   ├── api_keys.py           # API Key 管理
│   │   │   ├── datasets.py           # 数据集管理
│   │   │   ├── files.py              # 文件管理
│   │   │   ├── tasks.py              # 任务管理
│   │   │   ├── ai.py                 # AI 功能
│   │   │   ├── search.py             # 搜索功能
│   │   │   ├── statistics.py         # 统计功能
│   │   │   ├── tools.py              # 转换/导出工具
│   │   │   ├── backups.py            # 备份管理
│   │   │   ├── bugs.py               # Bug 标记
│   │   │   ├── monitoring.py         # 监控日志
│   │   │   ├── versions.py           # 版本管理
│   │   │   ├── transform.py          # 数据转换
│   │   │   ├── init.py               # 初始化向导
│   │   │   └── deps.py               # 依赖注入
│   │   │
│   │   ├── core/                     # 核心配置
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # 配置管理
│   │   │   ├── database.py           # 数据库连接
│   │   │   └── security.py           # 安全相关
│   │   │
│   │   ├── models/                   # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # 基础模型
│   │   │   ├── user.py               # 用户模型
│   │   │   ├── dataset.py            # 数据集模型
│   │   │   └── task.py               # 任务模型
│   │   │
│   │   ├── schemas/                  # Pydantic 模式
│   │   │   └── __init__.py
│   │   │
│   │   ├── services/                 # 业务服务
│   │   │   ├── __init__.py
│   │   │   ├── ai.py                 # AI 服务
│   │   │   ├── audit.py              # 审计服务
│   │   │   ├── backup.py             # 备份服务
│   │   │   ├── bugs.py               # Bug 服务
│   │   │   ├── conversion.py         # 格式转换
│   │   │   ├── download.py           # 下载服务
│   │   │   ├── export.py             # 导出服务
│   │   │   ├── init.py               # 初始化服务
│   │   │   ├── metadata.py           # 元数据提取
│   │   │   ├── schema_mapping.py     # Schema 映射
│   │   │   ├── script_execution.py   # 脚本执行
│   │   │   ├── version.py            # 版本管理
│   │   │   └── visualization.py      # 可视化服务
│   │   │
│   │   ├── main.py                   # 应用入口
│   │   └── worker.py                 # Celery Worker
│   │
│   ├── requirements.txt              # Python 依赖
│   └── pyproject.toml                # 项目配置
│
├── frontend/                         # 前端代码
│   ├── src/
│   │   ├── api/                      # API 客户端
│   │   │   └── index.ts
│   │   ├── layouts/                  # 布局组件
│   │   │   └── MainLayout.tsx
│   │   ├── pages/                    # 页面组件
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── InitWizard.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Datasets.tsx
│   │   │   ├── DatasetVisualizer.tsx
│   │   │   ├── ApiKeys.tsx
│   │   │   ├── AIAssistant.tsx
│   │   │   └── Settings.tsx
│   │   ├── stores/                   # 状态管理
│   │   │   └── auth.ts
│   │   ├── App.tsx                   # 应用入口
│   │   └── main.tsx                  # 渲染入口
│   │
│   └── package.json
│
├── docker/                           # Docker 配置
│   ├── docker-compose.yml
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── nginx.conf
│
├── docs/                             # 文档
│   └── PRD.md
│
├── README.md
└── agents/
    └── prd.json                      # PRD 源文件
```

---

## 后端模块详解

### 核心模块 (core)

#### config.py - 配置管理

**职责**：管理所有系统配置，支持环境变量和 .env 文件

**配置项**：
```python
PROJECT_NAME          # 项目名称
API_V1_PREFIX         # API 前缀 "/api/v1"
SECRET_KEY            # JWT 密钥
DATABASE_URL          # 数据库连接 URL
REDIS_URL             # Redis 连接 URL
DATA_STORAGE_PATH     # 数据存储路径
OPENROUTER_API_KEY    # LLM API Key
OPENROUTER_BASE_URL   # LLM API URL
OPENROUTER_MODEL      # 默认模型
ACCESS_TOKEN_EXPIRE_MINUTES  # Token 过期时间
```

---

#### database.py - 数据库连接

**职责**：管理数据库连接和会话

**主要函数**：
| 函数 | 说明 |
|------|------|
| `get_db()` | 获取数据库会话（依赖注入） |
| `init_db()` | 初始化数据库 |
| `close_db()` | 关闭数据库连接 |

---

#### security.py - 安全相关

**职责**：密码加密、JWT Token 管理

**主要函数**：
| 函数 | 说明 |
|------|------|
| `get_password_hash()` | 密码加密 |
| `verify_password()` | 密码验证 |
| `create_access_token()` | 创建 JWT Token |
| `decode_access_token()` | 解析 JWT Token |

---

### 数据模型 (models)

#### user.py - 用户模型

**模型定义**：

| 模型 | 说明 |
|------|------|
| `User` | 用户账户 |
| `APIKey` | API Key 管理 |

**User 字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| username | str | 用户名 |
| email | str | 邮箱 |
| hashed_password | str | 加密密码 |
| role | str | 角色 (admin/user) |
| is_active | bool | 是否激活 |

**APIKey 字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| user_id | int | 所属用户 |
| name | str | Key 名称 |
| key_hash | str | Key 哈希 |
| key_prefix | str | Key 前缀 (用于显示) |
| llm_api_url | str | 自定义 LLM URL |
| llm_api_key | str | 自定义 LLM Key |
| llm_model | str | 自定义模型 |
| quota_limit | int | 配额上限 |
| quota_used | int | 已使用配额 |

---

#### dataset.py - 数据集模型

**模型定义**：

| 模型 | 说明 |
|------|------|
| `Dataset` | 数据集容器 |
| `DataFile` | 单个数据文件 |
| `FileMetadata` | 文件元数据 |

**Dataset 字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| user_id | int | 所属用户 |
| name | str | 数据集名称 |
| description | str | 描述 |
| storage_path | str | 存储路径 |
| total_files | int | 文件总数 |
| total_size | int | 总大小 (bytes) |

**DataFile 字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| dataset_id | int | 所属数据集 |
| filename | str | 文件名 |
| relative_path | str | 相对路径 |
| file_size | int | 文件大小 |
| file_type | str | MIME 类型 |
| data_type | str | 数据类型 (image/video/text) |
| paired_text | str | 配对文本 |
| custom_metadata | JSON | 自定义元数据 |

---

#### task.py - 任务模型

**Task 字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| user_id | int | 所属用户 |
| task_type | str | 任务类型 |
| name | str | 任务名称 |
| status | str | 状态 (pending/running/completed/failed) |
| progress | int | 进度 (0-100) |
| input_params | JSON | 输入参数 |
| output_result | JSON | 输出结果 |
| error_message | str | 错误信息 |

**任务类型枚举**：
- `DOWNLOAD` - 下载任务
- `CONVERT` - 转换任务
- `EXPORT` - 导出任务
- `BACKUP` - 备份任务
- `METADATA_EXTRACT` - 元数据提取
- `VISUALIZATION` - 可视化生成

---

### API路由 (api)

#### deps.py - 依赖注入

**依赖函数**：
| 函数 | 说明 |
|------|------|
| `get_current_user()` | 获取当前登录用户 |
| `get_admin_user()` | 获取管理员用户（权限校验） |
| `check_initialized()` | 检查系统是否已初始化 |

---

#### auth.py - 认证 API

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/register | 用户注册 |
| POST | /auth/login | 用户登录 |
| GET | /auth/me | 获取当前用户信息 |
| POST | /auth/create-admin | 创建管理员 |

---

#### api_keys.py - API Key 管理

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api-keys | 列出用户的所有 Key |
| POST | /api-keys | 创建新 Key |
| DELETE | /api-keys/{id} | 删除 Key |
| POST | /api-keys/{id}/deactivate | 停用 Key |
| POST | /api-keys/{id}/reset-quota | 重置配额 |

---

#### datasets.py - 数据集管理

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /datasets | 列出数据集 |
| POST | /datasets | 创建数据集 |
| GET | /datasets/{id} | 获取数据集详情 |
| PATCH | /datasets/{id} | 更新数据集 |
| DELETE | /datasets/{id} | 删除数据集 |
| POST | /datasets/{id}/scan | 扫描数据集文件 |
| POST | /datasets/{id}/download/huggingface | 从 HuggingFace 下载 |
| POST | /datasets/{id}/download/url | 从 URL 下载 |
| GET | /datasets/{id}/files | 获取数据集文件列表 |

---

#### files.py - 文件管理

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /files/{id}/raw | 获取原始文件 |
| GET | /files/{id}/preview | 预览文件 |
| GET | /files/dataset/{id}/gallery | 获取数据集画廊 |
| POST | /files/{id}/extract-metadata | 提取元数据 |

---

#### tasks.py - 任务管理

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /tasks | 列出任务 |
| GET | /tasks/{id} | 获取任务详情 |
| POST | /tasks/{id}/cancel | 取消任务 |
| POST | /tasks/{id}/retry | 重试任务 |

---

#### ai.py - AI 功能

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /ai/generate-visualization | 生成可视化代码 |
| POST | /ai/generate-conversion-script | 生成转换脚本 |
| POST | /ai/analyze-quality/{dataset_id} | 分析数据质量 |
| POST | /ai/chat | AI 聊天助手 |

---

#### search.py - 搜索功能

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /search/files | 搜索文件 |
| GET | /search/datasets | 搜索数据集 |

---

#### statistics.py - 统计功能

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /statistics/overview | 统计概览 |
| GET | /statistics/timeline | 时间线统计 |
| GET | /statistics/dataset/{id} | 数据集统计 |

---

#### tools.py - 转换/导出工具

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /tools/datasets/{id}/convert | 格式转换 |
| POST | /tools/datasets/{id}/convert-annotations | 标注格式转换 |
| POST | /tools/files/{id}/transform-schema | Schema 映射转换 |
| POST | /tools/infer-mapping | 推断映射规则 |
| POST | /tools/validate-mapping | 验证映射规则 |
| POST | /tools/datasets/{id}/export | 导出数据集 |
| POST | /tools/datasets/{id}/export-training | 导出训练格式 |
| GET | /tools/exports | 列出导出任务 |

---

#### backups.py - 备份管理

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /backups/datasets/{id} | 备份数据集 |
| GET | /backups | 列出备份 |
| GET | /backups/{name} | 获取备份详情 |
| POST | /backups/{name}/restore | 恢复备份 |
| DELETE | /backups/{name} | 删除备份 |
| POST | /backups/prune | 清理旧备份 |
| GET | /backups/size | 获取备份大小 |

---

#### bugs.py - Bug 标记

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /bugs | 列出 Bug |
| POST | /bugs | 报告 Bug |
| POST | /bugs/bulk | 批量报告 |
| GET | /bugs/statistics | Bug 统计 |
| PATCH | /bugs/{id} | 更新 Bug 状态 |
| POST | /bugs/{id}/analyze | AI 分析 Bug |
| GET | /bugs/files/{id}/scan | 扫描文件 Bug |

---

#### monitoring.py - 监控日志

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /monitoring/audit-logs | 审计日志 |
| GET | /monitoring/metrics | 系统指标 |
| GET | /monitoring/health | 健康检查 |
| GET | /monitoring/stats | 系统状态 |
| GET | /monitoring/dashboard | 仪表盘数据 |
| POST | /monitoring/cleanup | 清理旧日志 |

---

#### versions.py - 版本管理

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /versions/info | 获取版本信息 |
| POST | /versions/datasets/{id} | 创建版本快照 |
| GET | /versions | 列出版本 |
| GET | /versions/{id} | 获取版本详情 |
| POST | /versions/{id}/restore | 恢复版本 |
| POST | /versions/compare | 比较版本差异 |

---

#### transform.py - 数据转换

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /transform/generate | AI 生成转换脚本 |
| POST | /transform/validate | 验证脚本安全性 |
| POST | /transform/test | 测试脚本 |
| POST | /transform/execute | 执行脚本 |
| POST | /transform/generate-and-execute | 一键生成执行 |
| GET | /transform/scripts | 列出保存的脚本 |
| GET | /transform/scripts/{name} | 获取脚本 |
| DELETE | /transform/scripts/{name} | 删除脚本 |

---

#### init.py - 初始化向导

**端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /init/status | 获取初始化状态 |
| POST | /init/initialize | 执行初始化 |
| GET | /init/config | 获取配置 |
| PUT | /init/config | 更新配置 |

---

### 业务服务 (services)

#### ai.py - AI 服务

**类**：`AIService`

**方法**：
| 方法 | 说明 |
|------|------|
| `generate_visualization_code()` | 生成可视化 HTML 代码 |
| `generate_conversion_script()` | 生成格式转换脚本 |
| `analyze_data_quality()` | 分析数据质量 |
| `chat()` | 通用聊天接口 |
| `analyze_bug()` | 分析 Bug 并给出建议 |

---

#### download.py - 下载服务

**类**：`DownloadService`

**方法**：
| 方法 | 说明 |
|------|------|
| `download_from_huggingface()` | 从 HuggingFace 下载数据集 |
| `download_from_url()` | 从 URL 下载文件 |

---

#### conversion.py - 格式转换服务

**类**：`ConversionService`

**方法**：
| 方法 | 说明 |
|------|------|
| `convert_format()` | 通用格式转换 (JSON/JSONL/CSV) |
| `convert_coco_to_yolo()` | COCO 转 YOLO 格式 |
| `convert_yolo_to_coco()` | YOLO 转 COCO 格式 |
| `convert_voc_to_coco()` | VOC 转 COCO 格式 |

---

#### schema_mapping.py - Schema 映射服务

**类**：`SchemaMappingService`

**方法**：
| 方法 | 说明 |
|------|------|
| `transform_schema()` | 执行 Schema 映射转换 |
| `infer_mapping()` | 自动推断映射规则 |
| `validate_mapping()` | 验证映射规则 |

---

#### script_execution.py - 脚本执行服务

**类**：`ScriptExecutionService`

**方法**：
| 方法 | 说明 |
|------|------|
| `validate_script()` | 验证脚本安全性 |
| `test_script()` | 沙箱测试脚本 |
| `execute_script()` | 执行转换脚本 |
| `save_script()` | 保存脚本 |
| `load_script()` | 加载脚本 |

---

#### metadata.py - 元数据提取服务

**类**：`MetadataService`

**方法**：
| 方法 | 说明 |
|------|------|
| `extract_image_metadata()` | 提取图片元数据 (EXIF) |
| `extract_video_metadata()` | 提取视频元数据 |
| `extract_text_metadata()` | 提取文本统计信息 |
| `extract_all()` | 自动识别并提取 |

---

#### visualization.py - 可视化服务

**类**：`VisualizationService`

**方法**：
| 方法 | 说明 |
|------|------|
| `generate_gallery()` | 生成图片画廊 HTML |
| `generate_preview()` | 生成文件预览 |
| `get_visualization_template()` | 获取可视化模板 |

---

#### backup.py - 备份服务

**类**：`BackupService`

**方法**：
| 方法 | 说明 |
|------|------|
| `create_backup()` | 创建备份 |
| `restore_backup()` | 恢复备份 |
| `list_backups()` | 列出备份 |
| `delete_backup()` | 删除备份 |
| `prune_old_backups()` | 清理旧备份 |

---

#### bugs.py - Bug 服务

**类**：`BugService`

**方法**：
| 方法 | 说明 |
|------|------|
| `report_bug()` | 报告 Bug |
| `update_bug_status()` | 更新状态 |
| `get_statistics()` | 获取统计 |
| `scan_file_for_bugs()` | 扫描文件问题 |

---

#### version.py - 版本服务

**类**：`VersionService`

**方法**：
| 方法 | 说明 |
|------|------|
| `create_version()` | 创建版本快照 |
| `restore_version()` | 恢复版本 |
| `compare_versions()` | 比较版本差异 |
| `init_dvc()` | 初始化 DVC |

---

#### audit.py - 审计服务

**类**：`AuditService`

**方法**：
| 方法 | 说明 |
|------|------|
| `log_action()` | 记录操作日志 |
| `get_logs()` | 获取日志 |
| `cleanup_old_logs()` | 清理旧日志 |

---

#### export.py - 导出服务

**类**：`ExportService`

**方法**：
| 方法 | 说明 |
|------|------|
| `export_dataset()` | 导出数据集 (ZIP/TAR) |
| `export_training_format()` | 导出训练格式 |
| `list_exports()` | 列出导出任务 |

---

#### init.py - 初始化服务

**类**：`InitService`

**方法**：
| 方法 | 说明 |
|------|------|
| `is_initialized()` | 检查是否已初始化 |
| `initialize()` | 执行初始化 |
| `get_init_status()` | 获取初始化状态 |
| `update_config()` | 更新配置 |

---

## 前端模块详解

### API 客户端 (api/index.ts)

**导出的 API 对象**：
| 对象 | 说明 |
|------|------|
| `authApi` | 认证相关 |
| `apiKeysApi` | API Key 管理 |
| `datasetsApi` | 数据集管理 |
| `tasksApi` | 任务管理 |
| `initApi` | 初始化 |
| `statisticsApi` | 统计数据 |
| `searchApi` | 搜索功能 |

---

### 页面组件 (pages/)

| 组件 | 说明 |
|------|------|
| `Login.tsx` | 登录页面 |
| `Register.tsx` | 注册页面 |
| `InitWizard.tsx` | 初始化向导 (5步) |
| `Dashboard.tsx` | 仪表盘主页 |
| `Datasets.tsx` | 数据集列表/管理 |
| `DatasetVisualizer.tsx` | 数据可视化 |
| `ApiKeys.tsx` | API Key 管理 |
| `AIAssistant.tsx` | AI 助手 |
| `Settings.tsx` | 系统设置 |

---

### 状态管理 (stores/auth.ts)

**使用 Zustand 管理认证状态**

| 状态 | 类型 | 说明 |
|------|------|------|
| token | string \| null | JWT Token |
| user | User \| null | 当前用户 |

| 方法 | 说明 |
|------|------|
| setToken() | 设置 Token |
| setUser() | 设置用户 |
| logout() | 登出 |

---

## API接口文档

### 认证模块

#### POST /api/v1/auth/login
**描述**：用户登录

**请求体**：
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**：
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

---

#### POST /api/v1/auth/register
**描述**：用户注册

**请求体**：
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

---

### 数据集模块

#### GET /api/v1/datasets
**描述**：列出数据集

**查询参数**：
- `page` - 页码 (默认 1)
- `page_size` - 每页数量 (默认 20)

---

#### POST /api/v1/datasets
**描述**：创建数据集

**请求体**：
```json
{
  "name": "string",
  "description": "string?",
  "storage_path": "string?"
}
```

---

### AI 模块

#### POST /api/v1/ai/chat
**描述**：AI 聊天

**请求体**：
```json
{
  "message": "string",
  "context": "string?",
  "api_key_override": "string?"
}
```

---

### 初始化模块

#### GET /api/v1/init/status
**描述**：获取初始化状态

**响应**：
```json
{
  "initialized": false,
  "data_path_configured": false,
  "admin_created": false,
  "missing_requirements": ["data_path", "admin_account"]
}
```

---

#### POST /api/v1/init/initialize
**描述**：执行初始化

**请求体**：
```json
{
  "data_path": "string (必填)",
  "admin_username": "string",
  "admin_email": "string (必填)",
  "admin_password": "string (必填)",
  "api_key": "string?",
  "api_model": "string?",
  "http_proxy": "string?"
}
```

---

## 数据库设计

### ER 图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │   Dataset   │       │  DataFile   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │───┐   │ id (PK)     │───┐   │ id (PK)     │
│ username    │   │   │ user_id(FK) │◄──┘   │ dataset_id  │◄──┐
│ email       │   │   │ name        │       │ filename    │   │
│ password    │   │   │ storage_path│       │ file_size   │   │
│ role        │   │   │ total_files │       │ data_type   │   │
└─────────────┘   │   └─────────────┘       └─────────────┘   │
      │           │                               │           │
      │           │                               ▼           │
      │           │                        ┌─────────────┐    │
      │           │                        │FileMetadata │    │
      │           │                        ├─────────────┤    │
      │           │                        │ id (PK)     │    │
      │           │                        │ data_file_id│◄───┘
      │           │                        │ width       │
      │           │                        │ height      │
      │           │                        │ duration    │
      │           │                        └─────────────┘
      │           │
      ▼           │
┌─────────────┐   │
│   APIKey    │   │
├─────────────┤   │
│ id (PK)     │   │
│ user_id(FK) │◄──┘
│ name        │
│ key_hash    │
│ quota_limit │
└─────────────┘

┌─────────────┐
│    Task     │
├─────────────┤
│ id (PK)     │
│ user_id(FK) │
│ task_type   │
│ status      │
│ progress    │
│ input_params│
│ output_result│
└─────────────┘
```

---

### 表关系

| 关系 | 类型 | 说明 |
|------|------|------|
| User → Dataset | 一对多 | 一个用户可有多个数据集 |
| User → APIKey | 一对多 | 一个用户可有多个 API Key |
| User → Task | 一对多 | 一个用户可有多个任务 |
| Dataset → DataFile | 一对多 | 一个数据集包含多个文件 |
| DataFile → FileMetadata | 一对一 | 一个文件有一条元数据记录 |

---

## 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                       Nginx (反向代理)                       │
│                    端口: 80/443                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│   Frontend      │         │    Backend      │
│   (React SPA)   │         │   (FastAPI)     │
│   端口: 3000    │         │   端口: 8000    │
└─────────────────┘         └────────┬────────┘
                                     │
                          ┌──────────┼──────────┐
                          ▼          ▼          ▼
                   ┌──────────┐ ┌──────────┐ ┌──────────┐
                   │ PostgreSQL│ │  Redis   │ │ 文件存储  │
                   │  端口:5432│ │ 端口:6379│ │ 本地/S3  │
                   └──────────┘ └──────────┘ └──────────┘
```

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 0.1.0 | 2026-03-09 | 初始版本，完成全部 21 个用户故事 |

---

*文档生成时间: 2026-03-09*

# 智能求职助手 FastAPI 部署说明

## 概述

本文档详细说明了如何将现有的Streamlit求职助手应用迁移到FastAPI框架，并进行部署。

## 项目结构

```
猎头/
├── fastapi_app/                 # FastAPI应用目录
│   ├── main.py                 # 主应用文件
│   ├── core/                   # 核心模块
│   │   ├── config.py          # 配置管理
│   │   ├── logging.py         # 日志配置
│   │   └── exceptions.py      # 异常处理
│   ├── api/                   # API路由
│   │   └── v1/
│   │       ├── api.py         # 路由汇总
│   │       └── endpoints/     # 具体端点
│   │           ├── conversation.py  # 对话管理
│   │           ├── rag.py          # RAG系统
│   │           ├── voice.py        # 语音交互
│   │           ├── documents.py    # 文档管理
│   │           └── health.py       # 健康检查
│   ├── schemas/               # Pydantic模型
│   │   ├── base.py           # 基础模型
│   │   ├── conversation.py   # 对话模型
│   │   ├── rag.py           # RAG模型
│   │   ├── voice.py         # 语音模型
│   │   └── documents.py     # 文档模型
│   └── middleware/           # 中间件
│       ├── timing.py        # 计时中间件
│       └── request_id.py    # 请求ID中间件
├── start_fastapi.py         # 启动脚本
├── test_fastapi.py          # 测试脚本
├── Dockerfile               # Docker配置
├── docker-compose.yml       # Docker Compose配置
├── nginx.conf              # Nginx配置
└── requirements.txt        # 依赖包
```

## 功能特性

### 1. 核心API功能
- **对话管理**: 多轮对话、会话状态管理
- **RAG系统**: 文档检索、智能问答
- **语音交互**: TTS/ASR、语音优化
- **文档管理**: 文件上传、向量化处理
- **健康检查**: 系统状态监控

### 2. 技术特性
- **异步处理**: 基于FastAPI的异步架构
- **数据验证**: Pydantic模型验证
- **错误处理**: 统一异常处理机制
- **日志记录**: 结构化日志系统
- **性能监控**: 请求计时、资源监控

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，配置API密钥等
```

### 2. 启动应用

```bash
# 开发模式启动
python start_fastapi.py

# 或使用uvicorn直接启动
uvicorn fastapi_app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问应用

- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

### 4. 测试应用

```bash
# 运行测试脚本
python test_fastapi.py
```

## Docker部署

### 1. 构建镜像

```bash
# 构建Docker镜像
docker build -t job-assistant-api .
```

### 2. 使用Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f job-assistant-api

# 停止服务
docker-compose down
```

### 3. 生产环境配置

```bash
# 生产环境启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## API使用示例

### 1. 开始对话

```bash
curl -X POST "http://localhost:8000/api/v1/conversation/start" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_user"}'
```

### 2. 发送消息

```bash
curl -X POST "http://localhost:8000/api/v1/conversation/message" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "your-session-id",
       "message": "我想找Python开发工程师的工作",
       "job_count": 3
     }'
```

### 3. RAG查询

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "有哪些Python开发的职位？",
       "k": 3
     }'
```

### 4. 职位搜索

```bash
curl -X POST "http://localhost:8000/api/v1/rag/search/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "job_type": "Python开发工程师",
       "location": "深圳",
       "salary": "15K-20K",
       "limit": 5
     }'
```

## 配置说明

### 1. 环境变量

```bash
# 基本配置
PROJECT_NAME=智能求职助手API
VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# 服务器配置
HOST=0.0.0.0
PORT=8000

# LLM配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=deepseek-r1

# 语音配置
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=your-azure-region
```

### 2. 日志配置

日志文件位置：
- 应用日志: `logs/app.log`
- 错误日志: `logs/error.log`

### 3. 存储配置

- 文档目录: `documents/`
- 向量存储: `vector_store/`
- 上传目录: `uploads/`

## 性能优化

### 1. 生产环境建议

```bash
# 使用多进程
uvicorn fastapi_app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 使用Gunicorn
gunicorn fastapi_app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 2. 缓存配置

- Redis缓存: 用于会话状态存储
- 响应缓存: 常用查询结果缓存

### 3. 监控配置

- Prometheus指标: `/metrics`
- 健康检查: `/health`
- 详细状态: `/api/v1/health/detailed`

## 故障排除

### 1. 常见问题

**问题**: 应用启动失败
**解决**: 检查环境变量配置，确保所有必需的API密钥已设置

**问题**: RAG系统初始化失败
**解决**: 检查documents目录是否存在文档文件，检查向量存储权限

**问题**: 语音功能不可用
**解决**: 检查Azure Speech Services配置

### 2. 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# Docker日志
docker-compose logs -f job-assistant-api
```

## 迁移对比

| 功能 | Streamlit版本 | FastAPI版本 |
|------|---------------|-------------|
| 用户界面 | Web界面 | RESTful API |
| 部署方式 | 单体应用 | 微服务架构 |
| 扩展性 | 有限 | 高度可扩展 |
| 性能 | 中等 | 高性能 |
| 集成能力 | 有限 | 强大 |
| 监控能力 | 基础 | 完善 |

## 后续开发

1. **前端开发**: 基于Vue.js或React的现代化前端
2. **WebSocket**: 实时对话功能
3. **认证授权**: JWT认证系统
4. **数据库集成**: PostgreSQL持久化存储
5. **缓存优化**: Redis缓存系统
6. **监控告警**: 完善的监控体系

## 支持

如有问题，请查看：
- API文档: http://localhost:8000/docs
- 项目日志: `logs/` 目录
- 测试脚本: `test_fastapi.py`

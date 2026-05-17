# 多源情报分析 Agent

基于 LangGraph + 通义千问 + ChromaDB 的多源情报分析系统。Agent 可自主调用**内部知识库**和**网络搜索**，生成结构化情报报告。

## 架构

```
用户输入
    │
    ▼
┌─────────────────┐
│  ReAct Agent     │  ← LangGraph + 通义千问 qwen-max
│  (自主决策)       │
└──────┬──────────┘
       │
       ├──→ 内部知识库 (ChromaDB + DashScope Embedding)
       │    └── 公司内部报告 / 简报
       │
       └──→ 网络搜索 (Tavily API)
            └── 公开新闻 / 网页
```

## 快速开始

### 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY 和 TAVILY_API_KEY

# 3. 构建内部知识库（可选）
python create_test_docs.py     # 生成测试文档
python build_knowledge_base.py # 向量化存入 ChromaDB

# 4. 运行
python multi_source_agent.py   # CLI 模式
python app.py                  # Web UI 模式
uvicorn api:app --port 8000    # API 模式
```

### Docker 运行

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY 和 TAVILY_API_KEY

# 2. 构建并启动（Gradio Web UI，默认端口 7860）
docker compose up -d

# 3. 构建知识库（首次运行需要）
docker compose exec intelligence-agent python create_test_docs.py
docker compose exec intelligence-agent python build_knowledge_base.py

# 4. 查看日志
docker compose logs -f

# 5. 改用 FastAPI 模式
# 编辑 docker-compose.yml，取消注释 command 行，注释掉默认 command
# 然后 docker compose up -d
```

- Web UI: http://localhost:7860
- API: http://localhost:8000/chat (FastAPI 模式)

## 功能

| 入口 | 说明 |
|------|------|
| `multi_source_agent.py` | 命令行交互，预设测试问题 |
| `app.py` | Gradio Web 界面，支持导出 Markdown / HTML 报告 |
| `api.py` | FastAPI REST 接口，`POST /chat` |

## 技术栈

- **Agent 框架**: LangGraph (ReAct Agent)
- **LLM**: 通义千问 qwen-max (DashScope)
- **向量库**: ChromaDB + text-embedding-v2
- **搜索**: Tavily API
- **UI**: Gradio / FastAPI

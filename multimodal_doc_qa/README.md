# Multimodal Document QA

基于 FastAPI + ChromaDB + DeepSeek 的多模态文档问答系统。支持 PDF 上传、文本提取、向量检索和 LLM 问答。

## 快速启动

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

## 接口

- `POST /ingest` — 上传 PDF 文件进行索引
- `POST /query` — `{"question":"..."}` 返回带来源的回答
- `GET /` — 前端页面

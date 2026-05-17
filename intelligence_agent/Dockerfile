FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY . .

# 创建知识库和数据目录
RUN mkdir -p knowledge_base_vectordb internal_docs

# 默认启动 Gradio Web UI
# 可覆盖：uvicorn api:app --host 0.0.0.0 --port 8000（FastAPI）
# 或：python build_knowledge_base.py && python multi_source_agent.py（CLI）
EXPOSE 7860 8000
CMD ["python", "app.py"]

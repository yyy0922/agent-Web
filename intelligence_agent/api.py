"""FastAPI 服务：将多源情报分析 Agent 暴露为 REST API。"""

import os
import asyncio

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent_core import run_agent, get_agent

app = FastAPI(title="多源情报分析 Agent API", version="1.0")

API_KEY = os.getenv("API_KEY", None)


class ChatRequest(BaseModel):
    message: str
    tools: list[str] = ["内部知识库", "网络搜索"]


async def authenticate(request: Request):
    if API_KEY and request.headers.get("x-api-key") != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")


async def collect_full_response(message: str, tools: list[str]) -> str:
    def invoke():
        stream = run_agent(message, tools)
        final_answer = ""
        for step in stream:
            for _node_name, data in step.items():
                if "messages" not in data:
                    continue
                last_msg = data["messages"][-1]
                if (
                    hasattr(last_msg, "type")
                    and last_msg.type == "ai"
                    and not (hasattr(last_msg, "tool_calls") and last_msg.tool_calls)
                ):
                    final_answer = last_msg.content
        if not final_answer:
            agent = get_agent(tools)
            result = agent.invoke({"messages": [{"role": "user", "content": message}]})
            final_answer = result["messages"][-1].content
        return final_answer

    return await asyncio.to_thread(invoke)


@app.post("/chat")
async def chat(request: Request, chat_req: ChatRequest):
    await authenticate(request)
    result = await collect_full_response(chat_req.message, chat_req.tools)
    return JSONResponse(content={"response": result})


@app.get("/health")
async def health():
    return {"status": "ok"}

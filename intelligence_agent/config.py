"""共享配置：LLM、向量知识库、工具、Agent 缓存。"""

import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.tools import TavilySearchResults
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# ========== 可选：LangSmith 追踪 ==========
if os.getenv("LANGSMITH_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

# ========== LLM ==========
llm = ChatTongyi(
    model="qwen-max",
    temperature=0.1,
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
)

# ========== 内部知识库 ==========
_db_path = str(Path(__file__).parent / "knowledge_base_vectordb")
vectorstore = Chroma(
    persist_directory=_db_path,
    embedding_function=DashScopeEmbeddings(
        model="text-embedding-v2",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    ),
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


def search_internal(query: str) -> str:
    docs = retriever.invoke(query)
    if not docs:
        return "内部知识库未找到相关信息。"
    return "\n\n".join(
        f"[来源：{doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )


internal_tool = Tool(
    name="内部知识库",
    func=search_internal,
    description="查询公司内部的独家分析报告、简报和战略文档。优先使用。",
)

# ========== 网络搜索 ==========
tavily_tool = TavilySearchResults(
    max_results=3,
    tavily_api_key=os.getenv("TAVILY_API_KEY"),
)

available_tools: dict[str, Tool] = {
    "内部知识库": internal_tool,
    "网络搜索": tavily_tool,
}

# ========== 系统提示 ==========
system_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的多源情报分析师，能够记住对话历史。你的工具根据用户选择而改变。
工作流程：
- 优先使用内部知识库，再补充网络搜索。
- 输出包含"内部情报"、"公开情报"、"综合分析"三部分的报告，并标注来源。
- 保持上下文连贯，可基于历史提问深入分析。"""),
    ("placeholder", "{messages}"),
])

# ========== Agent 工厂（带缓存）==========
agent_cache: dict[str, object] = {}
memory = MemorySaver()


def get_agent(tool_names: list[str]):
    key = ",".join(sorted(tool_names))
    if key not in agent_cache:
        tools = [available_tools[name] for name in tool_names if name in available_tools]
        agent = create_react_agent(llm, tools, prompt=system_prompt, checkpointer=memory)
        agent_cache[key] = agent
    return agent_cache[key]

"""CLI 入口：运行多源情报分析 Agent。"""

from config import llm, retriever, internal_tool, tavily_tool
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

# ---------- 构建工具列表 ----------
tools: list[Tool] = [internal_tool, tavily_tool]

# ---------- 系统提示 ----------
system_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的多源情报分析师。你有两个工具：
1. 内部知识库：包含公司内部的独家分析报告、简报和战略文档。
2. 网络搜索：可以获取公开的新闻、网页信息。

对于用户的每一个分析请求，请遵循以下工作流程：
- 第一步：先使用"内部知识库"工具，查看公司内部是否已有相关分析。内部信息是你的首要依据。
- 第二步：如果内部知识库信息不足或需要最新动态，再使用"网络搜索"工具获取公开信息进行补充。
- 第三步：综合内部和外部信息，生成一份清晰的分析报告。报告应包含"内部情报"、"公开情报"和"综合分析"三个部分，并标注信息来源。

如果你无法获取任何有效信息，请如实说明。"""),
    ("placeholder", "{messages}"),
])

# ---------- 创建 Agent ----------
agent_executor = create_react_agent(llm, tools, prompt=system_prompt)


def run_agent(query: str):
    print(f"用户问题：{query}\n")
    print("=" * 60)

    final_answer = ""

    for step in agent_executor.stream(
        {"messages": [{"role": "user", "content": query}]},
        config={"recursion_limit": 10},
    ):
        for _node_name, data in step.items():
            if "messages" not in data:
                continue
            last_msg = data["messages"][-1]
            if not hasattr(last_msg, "type"):
                continue

            if last_msg.type == "ai":
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    print(f"[Agent 决定调用工具] {last_msg.tool_calls}")
                else:
                    print(f"[Agent 回复] {last_msg.content}")
                    final_answer = last_msg.content
            elif last_msg.type == "tool":
                preview = str(last_msg.content)[:250]
                print(f"[工具返回] 来自 {last_msg.name} 的内容摘要：{preview}...")

    if not final_answer:
        result = agent_executor.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"recursion_limit": 10},
        )
        final_answer = result["messages"][-1].content

    print("\n" + "=" * 60)
    print("===最终分析报告===")
    print(final_answer)


if __name__ == "__main__":
    test_query = "请分析一下Nvidia在AI芯片市场面临的风险和竞争对手动态"
    run_agent(test_query)

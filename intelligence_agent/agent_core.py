"""Agent 核心：流式执行入口。"""

from config import get_agent, available_tools, memory


def run_agent(message: str, tool_choices: list[str] | None = None):
    """同步流式执行 Agent，返回 step 生成器。"""
    if tool_choices is None:
        tool_choices = list(available_tools.keys())
    agent = get_agent(tool_choices)
    config = {"configurable": {"thread_id": "main"}, "recursion_limit": 10}
    inputs = {"messages": [{"role": "user", "content": message}]}
    return agent.stream(inputs, config)

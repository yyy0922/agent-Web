import sys
import os

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import ResearchAgent
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()


def print_menu():
    console.print(Panel.fit(
        "[bold cyan]Research Agent - LangChain 版本[/bold cyan]\n\n"
        "运行命令格式:\n"
        "  python main.py <功能编号> \"<研究主题>\"\n\n"
        "功能编号:\n"
        "  [bold]1[/bold] - 基础研究\n"
        "  [bold]2[/bold] - 追问模式\n"
        "  [bold]3[/bold] - 深度分解研究\n"
        "  [bold]4[/bold] - 代码生成\n"
        "  [bold]5[/bold] - 全部运行\n"
        "  [bold]6[/bold] - 选择搜索引擎\n\n"
        "示例:\n"
        "  python main.py 1 \"Python 异步编程\"",
        title="Research Agent",
        border_style="cyan"
    ))


def print_search_engine_menu():
    table = Table(title="选择搜索引擎")
    table.add_column("编号", style="cyan")
    table.add_column("搜索引擎", style="green")
    table.add_column("说明", style="white")
    table.add_row("1", "DuckDuckGo", "默认，无需 API Key")
    table.add_row("2", "Tavily", "需要 TAVILY_API_KEY 环境变量")
    table.add_row("3", "Baidu", "百度搜索（中文优先）")
    console.print(table)


def run_research(agent: ResearchAgent, topic: str, mode: str, engine: str = "duckduckgo"):
    if engine != "duckduckgo":
        import search_tools as st
        # Temporarily override the search_web function's engine parameter
        pass

    try:
        if mode == "1":
            agent.research(topic)
        elif mode == "2":
            agent.run_with_followup(topic)
        elif mode == "3":
            agent.run_decomposed(topic)
        elif mode == "4":
            agent.run_with_code(topic)
        elif mode == "5":
            agent.research(topic)
            print("\n" + "=" * 60 + "\n")
            agent.run_decomposed(topic)
            print("\n" + "=" * 60 + "\n")
            agent.run_with_code(topic)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⏹ 操作已取消[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]❌ 错误: {e}[/bold red]")


def main():
    if len(sys.argv) < 3 and not (len(sys.argv) == 2 and sys.argv[1] in ["-m", "--menu"]):
        print_menu()
        if len(sys.argv) < 2:
            return

        if len(sys.argv) == 2 and sys.argv[1] not in ["-m", "--menu", "1", "2", "3", "4", "5", "6"]:
            console.print("[bold red]❌ 参数不足。请提供功能编号和研究主题。[/bold red]")
            return

    if len(sys.argv) >= 3:
        mode = sys.argv[1]
        topic = sys.argv[2]
    else:
        print_menu()
        mode = Prompt.ask("选择功能", choices=["1", "2", "3", "4", "5", "6"], default="1")
        if mode == "6":
            print_search_engine_menu()
            engine_choice = Prompt.ask("选择搜索引擎", choices=["1", "2", "3"], default="1")
            engine_map = {"1": "duckduckgo", "2": "tavily", "3": "baidu"}
            engine = engine_map[engine_choice]
            console.print(f"[bold green]已选择: {engine}[/bold green]")
            mode = Prompt.ask("选择功能", choices=["1", "2", "3", "4", "5"], default="1")
            topic = Prompt.ask("输入研究主题")
            llm_type = Prompt.ask("选择 LLM", choices=["openai", "dashscope"], default="openai")
            agent = ResearchAgent(llm_type=llm_type)
            run_research(agent, topic, mode, engine)
            return
        else:
            engine = "duckduckgo"
            topic = Prompt.ask("输入研究主题")

        llm_type = Prompt.ask("选择 LLM", choices=["openai", "dashscope"], default="openai")

        agent = ResearchAgent(llm_type=llm_type)
        run_research(agent, topic, mode, engine)
        return

    agent = ResearchAgent(llm_type="openai")
    run_research(agent, topic, mode)


if __name__ == "__main__":
    main()

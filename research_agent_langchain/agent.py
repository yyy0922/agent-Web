import os
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console

from search_tools import search_web
from web_loader import WebPageLoader
from llm import create_llm
from report_generator import save_report

# 控制台输出对象，用于在终端中打印彩色日志和交互提示
console = Console()

RESEARCH_SYSTEM_PROMPT = """你是一个专业的研究助手。请根据收集到的资料，生成一份结构清晰、内容详实的研究报告。

要求：
1. 报告必须包含：概述、核心发现、详细分析、总结
2. 使用客观、专业的语言
3. 引用资料来源
4. 如果资料不足，明确指出现有信息的局限性
5. 报告用中文撰写"""

FOLLOWUP_SYSTEM_PROMPT = """你是基于已有研究报告的问答助手。
请根据下面的报告内容和原始资料回答用户的追问。

要求：
1. 回答要基于已有报告和资料，不要编造信息
2. 如果问题超出已有资料范围，明确告知用户
3. 回答要详细、有深度
4. 用中文回答"""

DECOMPOSE_SYSTEM_PROMPT = """将一个研究主题拆解为 3~5 个具体的子问题。

要求：
1. 每个子问题要有可搜索性，覆盖不同方面
2. 子问题要具体、明确
3. 按逻辑顺序排列
4. 只输出子问题列表，每行一个"""

DECOMPOSE_REPORT_PROMPT = """你是一个专业的研究助手。请根据多角度搜索收集到的资料，生成一份综合研究报告。

要求：
1. 报告必须包含：概述、各子问题分析、综合结论
2. 从不同角度综合分析
3. 使用客观、专业的语言
4. 报告用中文撰写"""

CODE_GENERATION_SYSTEM_PROMPT = """你是一个 Python 开发专家。请根据研究内容生成有实际价值的 Python 代码。

要求：
1. 代码必须能直接运行（完整的脚本，不是片段）
2. 使用硬编码示例数据代替真实 API 调用
3. 包含必要的 import 和详细的 print() 输出
4. 代码要有实际学习或使用价值
5. 只输出 Python 代码块，用 ```python 包裹"""

# 上面的 prompt 常量用于构建不同任务类型的系统角色指令。
# 这些字符串将用于引导 LLM 生成研究报告、处理追问、拆解主题或生成示例代码。


class ResearchAgent:
    """研究代理类，封装搜索、抓取、报告生成、追问和代码生成流程。"""

    def __init__(self, llm_type: str = "openai"):
        """根据 llm_type 初始化不同的 LLM 客户端和网页加载器。"""
        if llm_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            self.llm = create_llm(
                model="gpt-4o-mini",
                api_key=api_key
            )
        elif llm_type == "dashscope":
            api_key = os.getenv("DASHSCOPE_API_KEY")
            self.llm = create_llm(
                model="qwen-plus",
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        else:
            raise ValueError(f"Unknown llm_type: {llm_type}")

        # 用于加载网页内容的辅助组件
        self.loader = WebPageLoader()

    def _search_and_fetch(self, query: str, max_sources: int = 8) -> list[str]:
        """搜索主题并抓取网页内容，返回多个来源的文本列表。"""
        results = search_web(query, max_results=max_sources)
        pages_content = []

        for i, r in enumerate(results):
            console.print(f"[dim]搜索 {i+1}/{len(results)}: {r.title}[/dim]")
            if r.url:
                # 尝试从搜索结果的 URL 中加载全文内容
                content = self.loader.load(r.url)
                if content and len(content) > 200:
                    pages_content.append(f"## 来源 {i+1}: {r.title}\nURL: {r.url}\n\n{content[:3000]}")

            # 如果已经收集到足够的来源，则提前停止
            if len(pages_content) >= max_sources:
                break

        if not pages_content:
            # 如果网页抓取失败，则回退为使用搜索摘要作为内容来源
            pages_content = [f"## 来源 {i+1}: {r.title}\n\n{r.snippet}" for i, r in enumerate(results[:max_sources])]

        return pages_content

    def _generate_report(self, topic: str, pages_content: list[str]) -> str:
        """基于收集到的资料构造提示并让 LLM 生成研究报告。"""
        context = "\n\n---\n\n".join(pages_content)

        prompt = ChatPromptTemplate.from_messages([
            ("system", RESEARCH_SYSTEM_PROMPT),
            ("human", "研究主题：{topic}\n\n收集到的资料：\n{context}")
        ])
        chain = prompt | self.llm | StrOutputParser()

        report = chain.invoke({"topic": topic, "context": context})
        return report

    def _build_sources_text(self, pages_content: list[str]) -> str:
        """将多个来源内容拼接成用于后续报告或追问的统一文本。"""
        return "\n\n---\n\n".join(pages_content)

    def research(self, topic: str, max_sources: int = 8) -> str:
        console.print(f"[bold cyan]🔍 开始研究: {topic}[/bold cyan]")

        pages_content = self._search_and_fetch(topic, max_sources)
        report = self._generate_report(topic, pages_content)
        filepath = save_report(topic, report)

        for line in report.split("\n")[:30]:
            console.print(line)

        console.print(f"\n[bold green]✅ 报告已保存: {filepath}[/bold green]")
        return report

    def _answer_followup(self, question: str, history: list) -> str:
        """根据已有对话历史回答用户追问，保持回答与已生成报告一致。"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", FOLLOWUP_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"input": question, "history": history})

    def run_with_followup(self, topic: str, max_sources: int = 8):
        console.print(f"[bold cyan]🔍 开始研究 (支持追问): {topic}[/bold cyan]")

        pages_content = self._search_and_fetch(topic, max_sources)
        report = self._generate_report(topic, pages_content)
        filepath = save_report(topic, report)

        for line in report.split("\n"):
            console.print(line)
        console.print(f"\n[bold green]✅ 报告已保存: {filepath}[/bold green]")

        sources_text = self._build_sources_text(pages_content)

        history = [AIMessage(content=f"报告：\n{report}\n\n原始资料：\n{sources_text}")]

        console.print("\n[bold yellow]💬 追问模式已启动（输入 n 退出）[/bold yellow]")
        while True:
            question = console.input("[bold cyan]📝 你的追问: [/bold cyan]").strip()
            if question.lower() == "n":
                break

            answer = self._answer_followup(question, history)
            console.print(f"[bold green]回答:[/bold green] {answer}")

            history.append(HumanMessage(content=question))
            history.append(AIMessage(content=answer))

    def _decompose_topic(self, topic: str) -> list[str]:
        """将一个研究主题拆解为若干可搜索的子问题。"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", DECOMPOSE_SYSTEM_PROMPT),
            ("human", "请拆解主题：{topic}")
        ])
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({"topic": topic})

        questions = [q.strip() for q in result.split("\n") if q.strip()]
        return questions[:6]

    def run_decomposed(self, topic: str, max_sources: int = 6) -> str:
        """针对拆解后的子问题逐个搜索并生成综合深度研究报告。"""
        console.print(f"[bold cyan]🔬 深度分解研究: {topic}[/bold cyan]")

        sub_questions = self._decompose_topic(topic)
        console.print(f"[bold yellow]拆解为 {len(sub_questions)} 个子问题:[/bold yellow]")
        for i, q in enumerate(sub_questions, 1):
            console.print(f"  {i}. {q}")

        all_pages = []
        for i, sub_q in enumerate(sub_questions, 1):
            console.print(f"\n[bold]--- 子问题 {i}/{len(sub_questions)}: {sub_q} ---[/bold]")
            pages = self._search_and_fetch(sub_q, max_sources)
            all_pages.extend(pages)

        context = "\n\n---\n\n".join(all_pages)

        prompt = ChatPromptTemplate.from_messages([
            ("system", DECOMPOSE_REPORT_PROMPT),
            ("human", "研究主题：{topic}\n\n多角度收集的资料：\n{context}")
        ])
        chain = prompt | self.llm | StrOutputParser()
        report = chain.invoke({"topic": topic, "context": context})

        filepath = save_report(f"{topic}_深度研究", report)

        for line in report.split("\n")[:40]:
            console.print(line)

        console.print(f"\n[bold green]✅ 深度研究报告已保存: {filepath}[/bold green]")
        return filepath

    def _generate_code(self, topic: str, pages: list[str], report: str) -> str:
        """向 LLM 请求生成可运行 Python 代码，并基于报告与来源内容进行约束。"""
        sources_text = self._build_sources_text(pages)

        prompt = ChatPromptTemplate.from_messages([
            ("system", CODE_GENERATION_SYSTEM_PROMPT),
            ("human", "研究主题：{topic}\n\n研究成果摘要：{report}\n\n收集到的资料：{sources}")
        ])
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"topic": topic, "report": report[:2000], "sources": sources_text[:3000]})

    def _save_code(self, topic: str, code_content: str) -> str:
        """保存生成的 Python 代码到 outputs 文件夹，并返回文件路径。"""
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in topic)
        safe_name = safe_name.strip().replace(" ", "_")[:40]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{safe_name}.py"
        filepath = os.path.join("outputs", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# 自动生成: {topic}\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(code_content)

        return filepath

    def _extract_code_block(self, text: str) -> str:
        """从模型返回的结果中提取```python```代码块内容，避免保存多余标记。"""
        if "```python" in text:
            start = text.index("```python") + len("```python")
            end = text.index("```", start) if "```" in text[start:] else len(text)
            return text[start:end].strip()
        return text.strip()

    def run_with_code(self, topic: str, max_sources: int = 6) -> str:
        """执行完整研究流程并生成可运行 Python 代码文件。"""
        console.print(f"[bold cyan]💻 研究并生成代码: {topic}[/bold cyan]")

        pages_content = self._search_and_fetch(topic, max_sources)
        report = self._generate_report(topic, pages_content)
        report_path = save_report(topic, report)

        code_result = self._generate_code(topic, pages_content, report)

        code = self._extract_code_block(code_result)
        code_path = self._save_code(topic, code)

        for line in report.split("\n")[:20]:
            console.print(line)

        console.print(f"\n[bold green]✅ 报告已保存: {report_path}[/bold green]")
        console.print(f"[bold green]✅ 代码已保存: {code_path}[/bold green]")

        console.print(f"\n[bold cyan]--- 生成的代码预览 ---[/bold cyan]")
        for line in code.split("\n")[:20]:
            console.print(line)

        return report_path




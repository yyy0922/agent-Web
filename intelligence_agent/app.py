"""Gradio Web UI：多源情报分析 Agent 交互界面。"""

import os
import markdown
import gradio as gr

from config import get_agent, available_tools

# ========== 流式处理 ==========
async def agent_stream(message, history, tool_choices):
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ""})
    yield history

    messages = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]
    config = {
        "configurable": {"thread_id": "main"},
        "recursion_limit": 10,
        "run_name": f"分析{message[:30]}",
    }
    inputs = {"messages": messages}

    final_answer = ""
    steps_display = []

    agent = get_agent(tool_choices)

    for step in agent.stream(inputs, config):
        for _node_name, data in step.items():
            if "messages" not in data:
                continue
            last_msg = data["messages"][-1]
            if not hasattr(last_msg, "type"):
                continue

            if last_msg.type == "ai":
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    tc = last_msg.tool_calls[0]
                    steps_display.append(
                        f"\U0001f527 调用工具：{tc['name']}，查询：{tc['args'].get('query', '')}"
                    )
                else:
                    final_answer = last_msg.content
            elif last_msg.type == "tool":
                summary = str(last_msg.content)[:200]
                steps_display.append(f"\U0001f4cb {last_msg.name} 返回摘要：{summary}...")

        partial = "\n".join(steps_display)
        if final_answer:
            partial += f"\n\n---\n{final_answer}"
        history[-1]["content"] = partial
        yield history

    if not final_answer:
        result = agent.invoke(inputs, config)
        final_answer = result["messages"][-1].content
        history[-1]["content"] = "\n".join(steps_display) + "\n\n---\n" + final_answer
        yield history


# ========== 导出功能 ==========
def _last_assistant_content(history):
    for msg in reversed(history):
        if msg["role"] == "assistant":
            c = msg["content"]
            if isinstance(c, list):
                return "\n".join(str(item) for item in c)
            return str(c)
    return None


def export_report_md(history):
    content = _last_assistant_content(history)
    if not content:
        return None
    filepath = "intelligence_report.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# 多源情报分析报告\n\n" + content)
    return filepath


def export_report_html(history):
    content = _last_assistant_content(history)
    if not content:
        return None
    md_content = "# 多源情报分析报告\n\n" + content
    html_body = markdown.markdown(md_content, extensions=["extra", "nl2br"])
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>多源情报分析报告</title>
<style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #1f2937; }}
    h1 {{ color: #1e3a8a; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }}
    h2 {{ color: #2563eb; }}
    h3 {{ color: #059669; }}
    p, li {{ font-size: 14px; line-height: 1.7; }}
    blockquote {{ border-left: 4px solid #2563eb; padding-left: 16px; margin: 1em 0; color: #4b5563; background: #f0f4ff; }}
    code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 13px; }}
    pre {{ background: #f1f5f9; padding: 16px; border-radius: 8px; overflow-x: auto; }}
    @media print {{ body {{ margin: 20px; }} }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
    filepath = "intelligence_report.html"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_html)
    return filepath


# ========== UI ==========
custom_css = """
.gradio-container { max-width: 950px !important; margin: auto; }
#title { text-align: center; font-size: 2.2em; font-weight: bold; margin: 0.5em 0 0.2em; }
.subtitle { text-align: center; color: #555; margin-bottom: 1.5em; }
footer { visibility: hidden; }
"""

with gr.Blocks(title="多源情报分析 Agent", css=custom_css) as demo:
    gr.HTML("<div id='title'>\U0001f575️ 多源情报分析 Agent</div>")
    gr.HTML(
        "<div class='subtitle'>输入任何公司、事件或问题，Agent 将综合内部知识库和网络搜索生成专业情报报告</div>"
    )

    chatbot = gr.Chatbot(label="情报对话", height=520, type="messages")

    with gr.Row():
        msg = gr.Textbox(
            placeholder="例如：分析 Nvidia 在 AI 芯片市场面临的风险和竞争对手动态...",
            label="你的提问",
            show_label=False,
            container=False,
            scale=4,
        )
        send = gr.Button("发送", variant="primary", scale=1)

    with gr.Row():
        source_choices = gr.CheckboxGroup(
            list(available_tools.keys()),
            label="\U0001f4e1 数据源选择",
            value=list(available_tools.keys()),
            interactive=True,
        )
    with gr.Row():
        clear = gr.Button("\U0001f5d1️ 清空")
        export_md = gr.Button("\U0001f4e5 导出 Markdown")
        export_html = gr.Button("\U0001f310 导出网页")
        download = gr.File(label="下载报告", visible=False)

    async def respond(message, history, tool_choices):
        async for updated_history in agent_stream(message, history, tool_choices):
            yield updated_history

    msg.submit(respond, [msg, chatbot, source_choices], chatbot)
    send.click(respond, [msg, chatbot, source_choices], chatbot)
    clear.click(lambda: [], None, chatbot, queue=False)
    export_md.click(export_report_md, chatbot, download).then(
        lambda: gr.update(visible=True), None, download
    )
    export_html.click(export_report_html, chatbot, download).then(
        lambda: gr.update(visible=True), None, download
    )

demo.queue()
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

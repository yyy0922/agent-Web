"""Gradio Web UI：多源情报分析 Agent 交互界面。"""

import os
import markdown
import gradio as gr

from config import get_agent, available_tools

# ========== 流式处理 ==========
async def agent_stream(message, history, tool_choices):
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": "⏳ **正在分析...**"})
    yield history

    messages = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]
    config = {
        "configurable": {"thread_id": "main"},
        "recursion_limit": 10,
        "run_name": f"分析{message[:30]}",
    }
    inputs = {"messages": messages}

    steps_log = []
    final_answer = ""
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
                    steps_log.append(
                        f"  <li>🔧 调用 <strong>{tc['name']}</strong>：<code>{tc['args'].get('query', '')}</code></li>"
                    )
                else:
                    final_answer = last_msg.content
            elif last_msg.type == "tool":
                summary = str(last_msg.content)[:150]
                steps_log.append(
                    f"  <li>📥 <strong>{last_msg.name}</strong> 返回：{summary}…</li>"
                )

        parts = []
        if steps_log:
            parts.append(
                "<details open>"
                "<summary style='font-weight:bold;cursor:pointer;color:#2563eb;font-size:0.95em;'>🔍 分析过程</summary>"
                "<ul style='padding-left:1.2em;color:#555;font-size:0.85em;line-height:1.6;'>{}</ul>"
                "</details>".format("".join(steps_log[-8:]))
            )
        if final_answer:
            parts.append(
                "<hr style='margin:0.8em 0;border:none;border-top:1px solid #e5e7eb;'>"
                "<div style='font-size:1em;line-height:1.7;'>{}</div>".format(
                    _render_markdown(final_answer)
                )
            )
        else:
            parts.append(
                "<div style='color:#999;font-style:italic;margin-top:0.4em;'>⏳ 正在收集信息...</div>"
            )

        history[-1]["content"] = "\n".join(parts)
        yield history

    if not final_answer:
        result = agent.invoke(inputs, config)
        final_answer = result["messages"][-1].content
        parts = []
        if steps_log:
            parts.append(
                "<details open>"
                "<summary style='font-weight:bold;cursor:pointer;color:#2563eb;font-size:0.95em;'>🔍 分析过程</summary>"
                "<ul style='padding-left:1.2em;color:#555;font-size:0.85em;line-height:1.6;'>{}</ul>"
                "</details>".format("".join(steps_log[-8:]))
            )
        parts.append(
            "<hr style='margin:0.8em 0;border:none;border-top:1px solid #e5e7eb;'>"
            "<div style='font-size:1em;line-height:1.7;'>{}</div>".format(
                _render_markdown(final_answer)
            )
        )
        history[-1]["content"] = "\n".join(parts)
        yield history


def _render_markdown(text: str) -> str:
    return markdown.markdown(text, extensions=["extra", "nl2br"])


# ========== 导出 ==========
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
    full_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>多源情报分析报告</title>
<style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #1f2937; }}
    h1 {{ color: #1e3a8a; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }}
    h2 {{ color: #2563eb; margin-top: 1.5em; }}
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


# ========== CSS ==========
custom_css = """
.gradio-container { max-width: 960px !important; margin: auto; padding-top: 0.5em !important; }
#page-title { text-align: center; font-size: 2em; font-weight: 700; margin: 0.3em 0 0.1em; color: #1e3a8a; letter-spacing: -0.02em; }
#page-subtitle { text-align: center; color: #6b7280; margin-bottom: 1em; font-size: 0.92em; }
footer { visibility: hidden; }
"""

SAMPLE_QUESTIONS = [
    "分析 Nvidia 在 AI 芯片市场的风险和竞争态势",
    "特斯拉 FSD 与国内自动驾驶方案对比",
    "2025 年全球半导体行业发展趋势",
]

# ========== UI ==========
with gr.Blocks(title="多源情报分析 Agent") as demo:
    gr.HTML("<div id='page-title'>\U0001f575️ 多源情报分析 Agent</div>")
    gr.HTML(
        "<div id='page-subtitle'>综合内部知识库 + 网络搜索，生成专业情报报告</div>"
    )

    chatbot = gr.Chatbot(label="对话", height=500)

    with gr.Row():
        msg = gr.Textbox(
            placeholder="输入分析主题，例如：分析 Nvidia 在 AI 芯片市场的风险...",
            label="提问",
            show_label=False,
            container=False,
            scale=6,
        )
        send = gr.Button("发送", variant="primary", scale=1, min_width=80)

    with gr.Row():
        source_choices = gr.CheckboxGroup(
            list(available_tools.keys()),
            label="\U0001f4e1 数据源",
            value=list(available_tools.keys()),
            interactive=True,
        )

    with gr.Row():
        clear = gr.Button("\U0001f5d1️ 清空对话", size="sm")
        export_md = gr.Button("\U0001f4e5 导出 Markdown", size="sm")
        export_html = gr.Button("\U0001f310 导出 HTML", size="sm")
        download = gr.File(label="下载", visible=False)

    gr.Markdown("---\n**\U0001f4a1 试试这些问题：**")
    sample_btns = []
    with gr.Row():
        for q in SAMPLE_QUESTIONS:
            sample_btns.append(gr.Button(q, size="sm"))

    # ========== 事件绑定 ==========
    async def respond(message, history, tool_choices):
        async for updated_history in agent_stream(message, history, tool_choices):
            yield updated_history

    # 发送 / 回车
    send.click(respond, [msg, chatbot, source_choices], chatbot).then(
        lambda: "", None, msg
    )
    msg.submit(respond, [msg, chatbot, source_choices], chatbot).then(
        lambda: "", None, msg
    )

    # 清空
    clear.click(lambda: ([], ""), None, [chatbot, msg], queue=False)

    # 导出
    export_md.click(export_report_md, chatbot, download).then(
        lambda: gr.update(visible=True), None, download
    )
    export_html.click(export_report_html, chatbot, download).then(
        lambda: gr.update(visible=True), None, download
    )

    # 示例按钮
    for btn in sample_btns:
        btn.click(fn=lambda q=btn.value: q, outputs=msg).then(
            respond, [msg, chatbot, source_choices], chatbot
        ).then(lambda: "", None, msg)

demo.queue()
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, css=custom_css, theme=gr.themes.Soft())

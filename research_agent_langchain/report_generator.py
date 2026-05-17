import os
from datetime import datetime


def save_report(topic: str, content: str, output_dir: str = "outputs") -> str:
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 过滤文件名中的非法字符，保留字母、数字、空格、下划线和连字符
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in topic)
    # 去除首尾空格、空格替换为下划线，并截断到50字符
    safe_name = safe_name.strip().replace(" ", "_")[:50]
    # 添加时间戳前缀，避免重名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{safe_name}.md"
    filepath = os.path.join(output_dir, filename)

    # 写入报告内容
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath



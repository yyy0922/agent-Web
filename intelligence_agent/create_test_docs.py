"""生成测试文档，用于构建内部知识库。"""

import os

docs_dir = "internal_docs"
os.makedirs(docs_dir, exist_ok=True)

content = """# 内部市场简报：Nvidia 与 AI 芯片竞争态势（2024 Q4）

## Nvidia 近况
- Nvidia 于 2024 年发布 Blackwell GPU 架构，性能较 Hopper 提升 2-5 倍。
- 数据中心业务营收同比增长 279%，达 145.1 亿美元。
- 公司计划使 GPU 更新节奏加快到"一年一架构"。

## 竞争对手动态
- AMD 推出 MI300X 加速器，声称在某些推理任务上超越 H100。
- 各大云厂商（Google、Amazon、Microsoft）均在自研 AI 芯片，如 Google TPU v5p、AWS Trainium2。
- 中国厂商华为昇腾 910B 在国内市场快速扩张，受限于制造工艺但生态逐渐完善。

## 风险与挑战
- 美国对华出口管制升级，可能进一步限制 Nvidia 特供芯片 H20 的销售。
- 客户集中度高：微软、Meta、亚马逊等前五大客户贡献超 40% 营收。
- 生成式 AI 应用端尚未出现杀手级应用，资本支出可持续性存疑。
"""

with open(os.path.join(docs_dir, "nvidia_ai_chip_analysis.md"), "w", encoding="utf-8") as f:
    f.write(content)

print("测试文档已生成：internal_docs/nvidia_ai_chip_analysis.md")

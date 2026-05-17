"""测试：从 ChromaDB 知识库中检索。"""

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma

db_dir = str(Path(__file__).parent / "knowledge_base_vectordb")
vectorstore = Chroma(
    persist_directory=db_dir,
    embedding_function=DashScopeEmbeddings(
        model="text-embedding-v2",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    ),
)

query = "Nvidia 在 AI 芯片市场面临哪些风险？"
results = vectorstore.similarity_search(query, k=2)

for i, doc in enumerate(results):
    print(f"=== Chunk {i+1} ===")
    print(doc.page_content)
    print(doc.metadata)
    print()

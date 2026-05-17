"""从 internal_docs/ 目录加载 Markdown 文件，构建 ChromaDB 知识库。"""

import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma

base_dir = Path(__file__).parent
docs_dir = str(base_dir / "internal_docs")
db_dir = str(base_dir / "knowledge_base_vectordb")

loader = DirectoryLoader(docs_dir, glob="**/*.md", loader_cls=TextLoader, show_progress=True)
documents = loader.load()
print(f"已加载 {len(documents)} 个文档")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=100,
    separators=["\n\n", "\n", "。", ".", " ", ""],
)
chunks = text_splitter.split_documents(documents)
print(f"已拆分为 {len(chunks)} 个文本块")

embeddings = DashScopeEmbeddings(
    model="text-embedding-v2",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
)

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=db_dir,
)
vectorstore.persist()
print("知识库构建成功！")

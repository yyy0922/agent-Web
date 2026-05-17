"""测试：加载 internal_docs/ 中的文档。"""

from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader

docs_dir = str(Path(__file__).parent / "internal_docs")
loader = DirectoryLoader(docs_dir, glob="**/*.md", loader_cls=TextLoader, show_progress=True)
documents = loader.load()

print(f"Loaded {len(documents)} documents")
for doc in documents:
    print(f"Source: {doc.metadata['source']}")
    print(doc.page_content[:200])
    print("---")

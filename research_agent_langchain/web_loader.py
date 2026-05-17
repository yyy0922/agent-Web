from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document


class WebPageLoader:
    def __init__(self):
        self.loader_class = WebBaseLoader

    def load(self, url: str) -> str:
        try:
            loader = self.loader_class(url)
            docs = loader.load()
            if docs:
                return docs[0].page_content
            return ""
        except Exception as e:
            print(f"[WARN] LangChain loader failed for {url}: {e}")
            return ""

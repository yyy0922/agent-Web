import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

CHROMA_DIR = os.environ.get("CHROMA_DIR", "./chroma_db")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

# DeepSeek 客户端（OpenAI 兼容格式）
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1") if DEEPSEEK_API_KEY else None


def _get_topk_context(question: str, k: int = 4, collection_name: str = "docs"):
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    q_emb = embed_model.encode(question).tolist()

    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        col = chroma_client.get_collection(collection_name)
    except Exception:
        return []

    results = col.query(query_embeddings=[q_emb], n_results=k)
    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    return list(zip(docs, metadatas))


def answer_question(question: str):
    ctx = _get_topk_context(question)
    context_text = "\n\n".join([f"Source: {m.get('source')}\n{d}" for d, m in ctx])

    if client:
        messages = [
            {"role": "system", "content": "你是一个文档助手。使用提供的文档内容来回答问题。如果答案不在文档中，请说'无法从文档中找到答案'。"},
            {"role": "user", "content": f"文档内容：\n{context_text}\n\n问题：{question}"}
        ]
        resp = client.chat.completions.create(model=LLM_MODEL, messages=messages, max_tokens=300)
        answer = resp.choices[0].message.content.strip()
    else:
        answer = "\n\n".join([d for d, _ in ctx]) or "无法从文档中找到答案"

    sources = [m.get("source") for _, m in ctx]
    return {"question": question, "answer": answer, "sources": list(dict.fromkeys(sources))}

import fitz  # pymupdf
from PIL import Image
from sentence_transformers import SentenceTransformer
from utils import chunk_text
import chromadb
import os

CHROMA_DIR = os.environ.get("CHROMA_DIR", "./chroma_db")


def extract_text_from_pdf(path: str):
    doc = fitz.open(path)
    pages = []
    for page in doc:
        text = page.get_text()
        if text and text.strip():
            pages.append(text)
        else:
            # attempt image OCR (requires tesseract installed)
            try:
                import pytesseract
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr = pytesseract.image_to_string(img)
                pages.append(ocr)
            except (ImportError, Exception):
                pages.append("[OCR unavailable — skipped image-based page]")
    return "\n\n".join(pages)


def ingest_file(path: str, collection_name: str = "docs"):
    text = extract_text_from_pdf(path)
    chunks = chunk_text(text, max_chars=1000)

    # embeddings
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = [embed_model.encode(c).tolist() for c in chunks]

    # chroma persistent client
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_or_create_collection(collection_name)

    ids = [f"{os.path.basename(path)}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": os.path.basename(path), "chunk_index": i} for i in range(len(chunks))]

    col.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)

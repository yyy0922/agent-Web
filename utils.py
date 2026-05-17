import textwrap


def chunk_text(text: str, max_chars: int = 1000):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for p in paragraphs:
        if len(p) <= max_chars:
            chunks.append(p)
        else:
            parts = textwrap.wrap(p, max_chars)
            chunks.extend(parts)
    return chunks

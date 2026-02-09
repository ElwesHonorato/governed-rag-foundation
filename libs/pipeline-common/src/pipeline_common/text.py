
import re


def chunk_text(text: str, *, target_size: int = 700) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            candidate = sentence if not current else f"{current} {sentence}"
            if len(candidate) > target_size and current:
                chunks.append(current)
                current = sentence
            else:
                current = candidate

    if current:
        chunks.append(current)

    return chunks

def chunk_text(
    text: str,
    chunk_size: int = 100,
    overlap: int = 20
) -> list[str]:
    words = text.split()

    if not words:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk = words[start:end]

        chunks.append(" ".join(chunk))

        # If this chunk already reached the end of the text,
        # there is no reason to create another overlapping chunk.
        if end >= len(words):
            break

        start += chunk_size - overlap

    return chunks
from app.models import NoteChunk


def build_rag_prompt(
    question: str,
    chunks: list[NoteChunk]
) -> str:
    context = "\n\n".join(
        chunk.content
        for chunk in chunks
    )

    return f"""
You are an AI study assistant.

Answer the user's question using only the provided context.

If the context does not contain enough information to answer,
say that you do not have enough information.

Context:
{context}

Question:
{question}

Answer:
""".strip()
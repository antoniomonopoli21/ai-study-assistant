from sqlalchemy.orm import Session

from app.models import NoteChunk
from app.services.chunking import chunk_text
from app.services.embeddings import embedding_service


EMBEDDING_DIMENSION = 384


def replace_note_chunks(
    db: Session,
    note_id: int,
    content: str,
    chunk_size: int = 100,
    overlap: int = 20
) -> None:
    db.query(NoteChunk).filter(
        NoteChunk.note_id == note_id
    ).delete()

    chunks = chunk_text(
        content,
        chunk_size=chunk_size,
        overlap=overlap
    )

    if not chunks:
        return

    embeddings = embedding_service.embed_passages(chunks)

    if len(embeddings) != len(chunks):
        raise ValueError(
            "Embedding count does not match chunk count"
        )

    for index, (chunk, embedding) in enumerate(
        zip(chunks, embeddings, strict=True)
    ):
        if len(embedding) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected embedding dimension "
                f"{EMBEDDING_DIMENSION}, got {len(embedding)}"
            )

        db_chunk = NoteChunk(
            note_id=note_id,
            chunk_index=index,
            content=chunk,
            embedding=embedding
        )

        db.add(db_chunk)
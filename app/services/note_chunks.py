from sqlalchemy.orm import Session

from app.models import NoteChunk
from app.services.chunking import chunk_text


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

    for index, chunk in enumerate(chunks):
        db_chunk = NoteChunk(
            note_id=note_id,
            chunk_index=index,
            content=chunk
        )

        db.add(db_chunk)
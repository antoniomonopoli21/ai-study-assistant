from sqlalchemy.orm import Session

from app.models import Note, NoteChunk
from app.services.embeddings import embedding_service


def search_similar_chunks(
    db: Session,
    user_id: int,
    query: str,
    limit: int = 3
) -> list[tuple[NoteChunk, float]]:
    query_embedding = embedding_service.embed_query(query)

    distance = NoteChunk.embedding.cosine_distance(
        query_embedding
    ).label("distance")

    results = (
        db.query(NoteChunk, distance)
        .join(Note, NoteChunk.note_id == Note.id)
        .filter(
            Note.user_id == user_id,
            NoteChunk.embedding.is_not(None)
        )
        .order_by(
            distance,
            NoteChunk.id
        )
        .limit(limit)
        .all()
    )

    return [
        (chunk, float(distance_value))
        for chunk, distance_value in results
    ]
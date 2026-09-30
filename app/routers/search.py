from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import SearchResult
from app.services.embeddings import EmbeddingServiceError
from app.services.retrieval import search_similar_chunks


router = APIRouter(
    prefix="/search",
    tags=["search"]
)


@router.get(
    "/",
    response_model=list[SearchResult]
)
def semantic_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        results = search_similar_chunks(
            db=db,
            user_id=current_user.id,
            query=q,
            limit=limit
        )
    except EmbeddingServiceError:
        raise HTTPException(
            status_code=503,
            detail="Embedding service temporarily unavailable"
        )

    return [
        SearchResult(
            note_id=chunk.note_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            distance=distance
        )
        for chunk, distance in results
    ]
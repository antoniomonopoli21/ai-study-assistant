from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import AskRequest, AskResponse, AskSource
from app.services.embeddings import EmbeddingServiceError
from app.services.llm import LLMServiceError, llm_service
from app.services.rag import RAG_INSTRUCTIONS, build_rag_prompt
from app.services.retrieval import search_similar_chunks


router = APIRouter(
    prefix="/ask",
    tags=["rag"]
)


@router.post(
    "/",
    response_model=AskResponse
)
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        results = search_similar_chunks(
            db=db,
            user_id=current_user.id,
            query=request.question,
            limit=request.limit
        )
    except EmbeddingServiceError:
        raise HTTPException(
            status_code=503,
            detail="Embedding service temporarily unavailable"
        )

    relevant_results = [
        (chunk, distance)
        for chunk, distance in results
        if distance <= settings.rag_max_distance
    ]

    if not relevant_results:
        return AskResponse(
            answer=(
                "I don't have enough information in your notes "
                "to answer that question."
            ),
            sources=[]
        )

    chunks = [
        chunk
        for chunk, distance in relevant_results
    ]

    prompt = build_rag_prompt(
        question=request.question,
        chunks=chunks
    )

    try:
        answer = llm_service.generate(
            prompt,
            instructions=RAG_INSTRUCTIONS
        )
    except LLMServiceError:
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable"
        )

    sources = [
        AskSource(
            note_id=chunk.note_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            distance=distance
        )
        for chunk, distance in relevant_results
    ]

    return AskResponse(
        answer=answer,
        sources=sources
    )
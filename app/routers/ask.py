from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import AskRequest, AskResponse, AskSource
from app.services.llm import llm_service
from app.services.rag import build_rag_prompt
from app.services.retrieval import search_similar_chunks

from app.config import settings

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
    results = search_similar_chunks(
        db=db,
        user_id=current_user.id,
        query=request.question,
        limit=request.limit
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

    answer = llm_service.generate(prompt)

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
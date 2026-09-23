from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas import NoteCreate, NoteResponse
from app.database import get_db
from app.models import Note


router = APIRouter(
    prefix = "/notes",
    tags = ["notes"]
)

@router.post(
    "/",
    status_code=201,
    response_model=NoteResponse
)
def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db)
):
    db_note = Note(
        subject=note.subject,
        title=note.title,
        content=note.content,
        priority=note.priority
    )

    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    return db_note


    

@router.get(
    "/",
    response_model=list[NoteResponse]
)
def get_notes(
    subject: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Note)

    if subject is not None:
        query = query.filter(Note.subject == subject)

    return query.all()




@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    db: Session = Depends(get_db)
    ):
    note = db.get(Note, note_id)

    if note is None:
        raise HTTPException(
            status_code = 404,
            detail = "Note not found"
    )
    return note



@router.put("/{note_id}",
            response_model= NoteResponse
            )
def update_note(
    note_id: int, 
    updated_note: NoteCreate,
    db: Session = Depends(get_db)
):
    note = db.get(Note, note_id)

    if note is None:
        raise HTTPException(
            status_code = 404,
            detail = "Note not found"
    )

    note.title = updated_note.title
    note.content = updated_note.content
    note.priority = updated_note.priority

    db.commit()
    db.refresh(note)

    return note

@router.delete("/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    note = db.get(Note, note_id)

    if note is None:
        raise HTTPException(
                status_code = 404,
                detail = "Note not found"
            )

    db.delete(note)
    db.commit()

    return{
            "message": "Note deleted successfully"
    }
    

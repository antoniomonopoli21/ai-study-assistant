from fastapi import APIRouter, HTTPException

from app.schemas import NoteCreate
from app import storage

router = APIRouter(
    prefix = "/notes",
    tags = ["notes"]
)

@router.post("/", status_code = 201)
def create_note(note: NoteCreate):

    note_data = {
        "id": storage.next_id,
        "title": note.title,
        "content": note.content,
        "priority": note.priority

    }
    storage.notes.append(note_data)
    storage.next_id += 1
    return note_data

@router.get("/")
def get_notes():
    return storage.notes


@router.get("//{note_id}")
def get_note(note_id: int):
    for note in storage.notes:
        if note["id"] == note_id:
            return note
    
    raise HTTPException(
        status_code = 404,
        detail = "Note not found"
    )



@router.put("/{note_id}")
def update_note(note_id: int, updated_note: NoteCreate):
    for note in storage.notes:
        if note["id"] == note_id:
            note["title"] = updated_note.title
            note["content"] = updated_note.content
            note["priority"] = updated_note.priority

            return note
    raise HTTPException(
        status_code = 404,
        detail = "Note not found"
    )

@router.delete("/{note_id}")
def delete_note(note_id: int):
    for note in storage.notes:
        if note["id"] == note_id:
            storage.notes.remove(note)

            return{
                "message": "Note deleted successfully"
            }
    raise HTTPException(
        status_code = 404,
        detail = "Note not found"
    )
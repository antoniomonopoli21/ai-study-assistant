from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Note(BaseModel):
    title: str
    content: str
    priority: int

notes = []
next_id = 1   

@app.get("/")
def root():
    return {"message": "AI Study Assistant API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/notes", status_code = 201)
def create_note(note: Note):
    global next_id

    note_data = {
        "id": next_id,
        "title": note.title,
        "content": note.content,
        "priority": note.priority

    }

    notes.append(note_data)
    next_id += 1
    return note_data

@app.get("/notes/{note_id}")
def get_note(note_id: int):
    for note in notes:
        if note["id"] == note_id:
            return note
    
    raise HTTPException(
        status_code = 404,
        detail = "Note not found"
    )
    

@app.get("/notes")
def get_notes():
    return notes

@app.put("/notes/{note_id}")
def update_note(note_id: int, updated_note: Note):
    for note in notes:
        if note["id"] == note_id:
            note["title"] = updated_note.title
            note["content"] = updated_note.content
            note["priority"] = updated_note.priority

            return note
    raise HTTPException(
        status_code = 404,
        detail = "Note not found"
    )

@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    for note in notes:
        if note["id"] == note_id:
            notes.remove(note)

            return{
                "message": "Note deleted successfully"
            }
    raise HTTPException(
        status_code = 404,
        detail = "Note not found"
    )
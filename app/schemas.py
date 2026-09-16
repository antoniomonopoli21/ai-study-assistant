from pydantic import BaseModel

class NoteCreate(BaseModel):
    title: str
    content: str
    priority: int

class NoteResponse(NoteCreate):
    id: int

    
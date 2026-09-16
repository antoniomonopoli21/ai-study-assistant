from pydantic import BaseModel, ConfigDict

class NoteCreate(BaseModel):
    title: str
    content: str
    priority: int

class NoteResponse(NoteCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)

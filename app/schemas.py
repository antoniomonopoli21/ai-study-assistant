from pydantic import BaseModel, ConfigDict
from datetime import datetime

class NoteCreate(BaseModel):
    title: str
    content: str
    priority: int

class NoteResponse(NoteCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

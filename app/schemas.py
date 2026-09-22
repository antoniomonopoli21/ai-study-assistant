from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

class NoteCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    priority: int = Field(ge=1, le=5)

    @field_validator("subject", "title")
    @classmethod
    def validate_title(cls, value: str):
        if not value.strip():
            raise ValueError("Field cannot be empty")

        return value

class NoteResponse(NoteCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

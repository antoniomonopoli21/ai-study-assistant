from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class NoteCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50_000)
    priority: int = Field(ge=1, le=5)

    @field_validator("subject", "title", "content")
    @classmethod
    def validate_not_blank(cls, value: str):
        if not value.strip():
            raise ValueError("Field cannot be empty")

        return value.strip()


class NoteResponse(NoteCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value


class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class SearchResult(BaseModel):
    note_id: int
    chunk_index: int
    content: str
    distance: float


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=1_000
    )
    limit: int = Field(default=3, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str):
        if not value.strip():
            raise ValueError("Question cannot be empty")

        return value.strip()


class AskSource(BaseModel):
    note_id: int
    chunk_index: int
    content: str
    distance: float


class AskResponse(BaseModel):
    answer: str
    sources: list[AskSource]
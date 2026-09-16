from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title : Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default=func.now()
    )

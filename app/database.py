from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.database_url import get_database_url

engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={
        "connect_timeout": 5,
    },
)

SessionLocal = sessionmaker(
    bind = engine,
    autoflush = False,
    autocommit = False
)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally: 
        db.close()
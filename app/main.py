from fastapi import FastAPI

from app.routers.notes import router as notes_router
from app.database import Base, engine
from app import models

Base.metadata.create_all(bind = engine)

app = FastAPI()

app.include_router(notes_router)


@app.get("/")
def root():
    return {"message": "AI Study Assistant API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


    




from fastapi import FastAPI

from app.routers.notes import router as notes_router
from app.routers.auth import router as auth_router

from app.routers import search


app = FastAPI()

app.include_router(notes_router)
app.include_router(auth_router)
app.include_router(search.router)

@app.get("/")
def root():
    return {"message": "AI Study Assistant API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


    




from fastapi import FastAPI

from app.routers.notes import router as notes_router
from app.routers.auth import router as auth_router



app = FastAPI()

app.include_router(notes_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "AI Study Assistant API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


    




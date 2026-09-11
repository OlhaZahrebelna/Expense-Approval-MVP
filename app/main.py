from fastapi import FastAPI

from app.database import Base, engine
from app.auth import router as auth_router
from app import models


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Approval MVP",
    version="0.1.0"
)

app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

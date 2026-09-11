from fastapi import FastAPI

from app.database import Base, engine
from app.auth import router as auth_router
from app.expenses import router as expenses_router
from app import models

from app.seed import seed

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Approval MVP",
    version="0.1.0"
)

app.include_router(auth_router)
app.include_router(expenses_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/admin/seed")
def run_seed():
    seed()
    return {"status": "seed completed"}
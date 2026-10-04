from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import SessionLocal
from app.database import create_db
from app.routers import payments
from app.routers import tariffs
from app.routers import webhooks
from app.services import seed_tariffs

@asynccontextmanager
async def lifespan(app: FastAPI):

    create_db()

    db = SessionLocal()
    seed_tariffs(db)

    db.close()

    yield


app = FastAPI(
    title="Kvitto Payments API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(tariffs.router)
app.include_router(payments.router)
app.include_router(webhooks.router)
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlalchemy import select

from app import models
from app.database import Base, SessionLocal, engine
from app.logging_setup import setup_logging
from app.routers import calender, folders, settings, todos, voice

setup_logging()
access_log = logging.getLogger("koe.access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Erstellt die Tabellen, falls sie noch nicht existieren."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as database:
        folder = database.scalar(select(models.Folder).where(models.Folder.is_system))
        # Systemordner und settings anlegen
        if folder is None:
            database.add_all(
                [
                    models.Folder(name="Allgemein", color="#4169E1", is_system=True, position=0),
                ]
            )

        if database.get(models.ServerSettings, 1) is None:
            database.add(models.ServerSettings())

        database.commit()

    yield


koe = FastAPI(title="Koe", lifespan=lifespan)


@koe.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        ms = (time.perf_counter() - start) * 1000
        access_log.exception("%s %s -> 500 (%.0f ms)", request.method, request.url.path, ms)
        raise
    ms = (time.perf_counter() - start) * 1000
    access_log.info("%s %s %d %.0fms", request.method, request.url.path, response.status_code, ms)
    return response


@koe.get("/health")
def health():
    return {"status": "ok"}


for r in (folders, todos, settings, voice, calender):
    koe.include_router(r.router)
from contextlib import asynccontextmanager

from sqlalchemy import select

from fastapi import FastAPI


from app import models
from app.database import Base, SessionLocal, engine
from app.routers import calender, folders, settings, todos, voice


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Erstellt die Tabellen, falls sie noch nicht existieren."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as database:

        folder = database.scalar(select(models.Folder).where(models.Folder.is_system))
        if folder is None:
            # Systemordner uns settings anlegen
            database.add_all(
                [
                    models.Folder(name="Allgemein", color="#4169E1", is_system=True, position=0),
                ]
            )
            database.commit()

        if database.get(models.Settings, 1) is None:
            database.add(models.Settings())
    yield

koe = FastAPI(title="Koe", lifespan=lifespan)


@koe.get("/health")
def health():
    return {"status": "ok"}


for r in (folders, todos, settings, voice, calender):
    koe.include_router(r.router)
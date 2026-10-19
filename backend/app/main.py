from contextlib import asynccontextmanager

from FASTAPI import FastAPI


from app import models
from app.database import Base, SessionLocal, engine
from app.routers import calender, folders, settings, todos, voice


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Erstellt die Tabellen, falls sie noch nicht existieren."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as database:

        database.scalar(select(models.Folder).where(Folder.is_system))
        if fodler is None:
            # Systemordner anlegen
            database.add_all(
                [
                    models.Folder(name="Allgemein", color="#4169E1", is_system=True, position=0),
                ]
            )
            database.commit()
    yield
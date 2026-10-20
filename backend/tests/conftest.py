import os

# Muss vor dem Import der App stehen, sonst liest EnvSettings die echte .env
os.environ["DATABASE_URL"] = "postgresql+psycopg://x:x@127.0.0.1:5432/x"  # wird nie benutzt
os.environ["API_TOKEN"] = "test-token"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import koe
from app.config import env


@pytest.fixture
def db():
    engine = create_engine(env.test_database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(models.Folder(name="Allgemein", color="#4169E1", is_system=True, position=0))
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db):
    koe.dependency_overrides[get_db] = lambda: db
    # Ohne `with`, damit lifespan (und damit Postgres) nicht startet
    yield TestClient(koe, headers={"Authorization": "Bearer test-token"})
    koe.dependency_overrides.clear()
import os
from collections.abc import Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.constants import TARIFFS
from app.database import Base
from app.database import get_db
from app.main import app
from app.models import Tariff


load_dotenv()


TEST_DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("TEST_DB_USER"),
    password=os.getenv("TEST_DB_PASSWORD"),
    host=os.getenv("TEST_DB_HOST", "127.0.0.1"),
    port=int(os.getenv("TEST_DB_PORT", "5432")),
    database=os.getenv("TEST_DB_NAME", "kvitto_test"),
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
def prepare_database() -> Generator[None, None, None]:
    """
    Перед каждым тестом:
    1. удаляет прежние таблицы;
    2. создаёт чистые таблицы;
    3. добавляет три тарифа.

    После теста удаляет таблицы.
    """
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        for tariff_data in TARIFFS:
            db.add(
                Tariff(
                    title=tariff_data["title"],
                    price=tariff_data["price"],
                )
            )

        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
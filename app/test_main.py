import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app, get_db_session


@pytest.fixture(name="db_session")
def db_session_fixture():
    engine = create_engine(  
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
         yield session


@pytest.fixture(name="client")
def client_fixture(db_session: Session):
    def get_db_session_override():
        return db_session

    app.dependency_overrides[get_db_session] = get_db_session_override
    
    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


def test_create_hero(client: TestClient):
        request_body = {
            "name": "Pedro Parques",
            "secret_name": "Spoder-Man",
        }

        response = client.post("/heroes/", json=request_body)
        
        data = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert data["name"] == "Pedro Parques"
        assert data["secret_name"] == "Spoder-Man"
        assert data["age"] is None
        assert data["id"] is not None


def test_create_hero_incomplete(client: TestClient):
    response = client.post("/heroes/", json={"name": "Pedro Parques"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_hero_invalid(client: TestClient):
    request_body = {
            "name": "Pedro Parques",
            "secret_name": {
                 "message": "Nah"
            },
        }
    response = client.post("/heroes/", json=request_body)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

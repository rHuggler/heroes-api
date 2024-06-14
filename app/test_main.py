import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import Hero, app, get_db_session


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


@pytest.fixture(name="hero")
def create_example_hero(db_session: Session):
    hero = Hero(name="Pedro Parques", secret_name="Spoder-Man")
    db_session.add(hero)
    db_session.commit()
    db_session.refresh(hero)

    yield hero


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


def test_read_heroes(db_session: Session, client: TestClient, hero: Hero):
    hero_1 = hero
    hero_2 = Hero(name="Nicolas Cage", secret_name="Nicol Bolas", age=48)
    db_session.add(hero_2)
    db_session.commit()

    response = client.get("/heroes/")
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2
    assert data[0]["name"] == hero_1.name
    assert data[0]["secret_name"] == hero_1.secret_name
    assert data[0]["age"] == hero_1.age
    assert data[0]["id"] == hero_1.id
    assert data[1]["name"] == hero_2.name
    assert data[1]["secret_name"] == hero_2.secret_name
    assert data[1]["age"] == hero_2.age
    assert data[1]["id"] == hero_2.id


def test_read_hero(client: TestClient, hero: Hero):    
    response = client.get(f"/heroes/{hero.id}")
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["name"] == hero.name
    assert data["secret_name"] == hero.secret_name
    assert data["age"] == hero.age
    assert data["id"] == hero.id


def test_update_hero(client: TestClient, hero: Hero):
    request_body = {
        "name": "Pedro Parques",
        "secret_name": "Spider-Man",
    }
    response = client.patch(f"/heroes/{hero.id}", json=request_body)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["name"] == hero.name
    assert data["secret_name"] == hero.secret_name
    assert data["age"] == hero.age
    assert data["id"] == hero.id


def test_delete_hero(client: TestClient, hero: Hero):
    response = client.delete(f"/heroes/{hero.id}")
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["ok"] == True

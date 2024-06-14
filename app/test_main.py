import copy

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.dependencies.database import get_db_session
from app.models.hero import Hero
from app.models.team import Team


@pytest.fixture(name="db_session")
def db_session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
    hero = Hero(name="Pedro Parques", secret_name="Spoder-Man", age=21, team_id=1)
    db_session.add(hero)
    db_session.commit()
    db_session.refresh(hero)

    yield hero


@pytest.fixture(name="team")
def create_example_team(db_session: Session):
    team = Team(name="Liga das Lendas", headquarters="Sorocaba")
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)

    yield team


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
        "secret_name": {"message": "Nah"},
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


def test_read_missing_hero(client: TestClient):
    response = client.get("/heroes/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_hero(client: TestClient, hero: Hero):
    request_body = {
        "name": "Pedro Parques",
        "secret_name": "Spider-Man",
    }

    previous_hero = copy.deepcopy(hero)

    response = client.patch(f"/heroes/{hero.id}", json=request_body)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["name"] == hero.name
    assert data["secret_name"] == hero.secret_name
    assert data["age"] == hero.age
    assert data["id"] == hero.id
    assert data["name"] == previous_hero.name
    assert data["secret_name"] != previous_hero.secret_name


def test_update_missing_hero(client: TestClient):
    request_body = {
        "name": "Pedro Parques",
        "secret_name": "Spider-Man",
    }
    response = client.patch("/heroes/999", json=request_body)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_hero(db_session: Session, client: TestClient, hero: Hero):
    response = client.delete(f"/heroes/{hero.id}")
    data = response.json()

    db_hero = db_session.get(Hero, hero.id)

    assert response.status_code == status.HTTP_200_OK
    assert data["ok"] == True
    assert db_hero is None


def test_delete_missing_hero(client: TestClient):
    response = client.delete("/heroes/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_team(client: TestClient):
    request_body = {
        "name": "Liga das Legendas",
        "headquarters": "Sorocaba",
    }
    response = client.post("/teams/", json=request_body)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["name"] == "Liga das Legendas"
    assert data["headquarters"] == "Sorocaba"
    assert data["id"] is not None


def test_create_team_incomplete(client: TestClient):
    response = client.post("/teams/", json={"name": "Liga das Legendas"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_team_invalid(client: TestClient):
    request_body = {
        "name": "Liga das Legendas",
        "headquarters": {"message": "Nah"},
    }
    response = client.post("/teams/", json=request_body)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_read_teams(db_session: Session, client: TestClient, team: Team):
    team_1 = team
    team_2 = Team(name="Nicolas Cage", headquarters="Nicol Bolas")
    db_session.add(team_2)
    db_session.commit()

    response = client.get("/teams/")
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2
    assert data[0]["name"] == team_1.name
    assert data[0]["headquarters"] == team_1.headquarters
    assert data[0]["id"] == team_1.id
    assert data[1]["name"] == team_2.name
    assert data[1]["headquarters"] == team_2.headquarters
    assert data[1]["id"] == team_2.id


def test_read_team(client: TestClient, team: Team):
    response = client.get(f"/teams/{team.id}")
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["name"] == team.name
    assert data["headquarters"] == team.headquarters
    assert data["id"] == team.id


def test_read_missing_team(client: TestClient):
    response = client.get("/teams/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_team(client: TestClient, team: Team):
    request_body = {
        "name": "Liga das Legendas",
    }

    previous_team = copy.deepcopy(team)

    response = client.patch(f"/teams/{team.id}", json=request_body)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["name"] == team.name
    assert data["headquarters"] == team.headquarters
    assert data["id"] == team.id
    assert data["headquarters"] == previous_team.headquarters
    assert data["name"] != previous_team.name


def test_update_missing_team(client: TestClient):
    request_body = {
        "name": "Liga das Legendas",
    }
    response = client.patch("/teams/999", json=request_body)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_team(db_session: Session, client: TestClient, team: Team):
    response = client.delete(f"/teams/{team.id}")
    data = response.json()

    db_team = db_session.get(Team, team.id)

    assert response.status_code == status.HTTP_200_OK
    assert data["ok"] == True
    assert db_team is None


def test_delete_missing_team(client: TestClient):
    response = client.delete("/teams/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_hero_populates_team(client: TestClient, hero: Hero, team: Team):
    response = client.get(f"/heroes/{hero.id}")
    data = response.json()

    assert data["team"]["name"] == team.name


def test_team_populates_heroes(client: TestClient, hero: Hero, team: Team):
    response = client.get(f"/teams/{team.id}")
    data = response.json()

    assert data["heroes"][0]["name"] == hero.name

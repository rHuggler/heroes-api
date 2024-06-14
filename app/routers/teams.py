from fastapi import Depends, HTTPException, Query
from fastapi.routing import APIRouter
from sqlmodel import Session, select

from app.models.team import Team, TeamCreate, TeamUpdate, TeamPublic
from app.models.related import TeamPublicWithHeroes
from app.dependencies.database import get_db_session

team_router = APIRouter()

@team_router.post("/teams", response_model=TeamPublic)
def create_team(*, session: Session = Depends(get_db_session), team: TeamCreate):
    db_team = Team.model_validate(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@team_router.get("/teams", response_model=list[TeamPublic])
def read_teams(
    *,
    session: Session = Depends(get_db_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    teams = session.exec(select(Team).offset(offset).limit(limit)).all()
    return teams


@team_router.get("/teams/{team_id}", response_model=TeamPublicWithHeroes)
def read_team(*, session: Session = Depends(get_db_session), team_id: int):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@team_router.patch("/teams/{team_id}", response_model=TeamPublic)
def update_team(
    *, session: Session = Depends(get_db_session), team_id: int, team: TeamUpdate
):
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    team_data = team.model_dump(exclude_unset=True)
    db_team.sqlmodel_update(team_data)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@team_router.delete("/teams/{team_id}")
def delete_team(*, session: Session = Depends(get_db_session), team_id: int):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    session.delete(team)
    session.commit()
    return {"ok": True}

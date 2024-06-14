from fastapi import Depends, HTTPException, Query
from fastapi.routing import APIRouter
from sqlmodel import Session, select

from app.models.hero import Hero, HeroCreate, HeroUpdate, HeroPublic
from app.models.related import HeroPublicWithTeam
from app.dependencies.database import get_db_session

hero_router = APIRouter()

@hero_router.post("/heroes", response_model=HeroPublic)
def create_hero(*, session: Session = Depends(get_db_session), hero: HeroCreate):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@hero_router.get("/heroes", response_model=list[HeroPublic])
def read_heroes(
    *,
    session: Session = Depends(get_db_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


@hero_router.get("/heroes/{hero_id}", response_model=HeroPublicWithTeam)
def read_hero(*, session: Session = Depends(get_db_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@hero_router.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(
    *, session: Session = Depends(get_db_session), hero_id: int, hero: HeroUpdate
):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@hero_router.delete("/heroes/{hero_id}")
def delete_hero(*, session: Session = Depends(get_db_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}


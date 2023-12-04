from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query
from sqlmodel import Field, Relationship, Session, SQLModel, select

from db import create_db_and_tables, get_session


# Team models ###
class TeamBase(SQLModel):
    name: str = Field(index=True)
    headquarters: str


class Team(TeamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    heroes: list["Hero"] = Relationship(back_populates="team")


class TeamCreate(TeamBase):
    pass


class TeamRead(TeamBase):
    id: int


class TeamUpdate(SQLModel):
    id: int | None = None
    name: str | None = None
    headquarters: str | None = None


# End Team models ###


# Hero models ###
class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)

    team_id: int | None = Field(default=None, foreign_key="team.id")


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    team: Team | None = Relationship(back_populates="heroes")


class HeroRead(HeroBase):
    id: int


class HeroCreate(HeroBase):
    pass


class HeroUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None
    team_id: int | None = None


# End Hero models ###


# Hero and Team link models ###
class HeroReadWithTeam(HeroRead):
    team: TeamRead | None = None


class TeamReadWithHeroes(TeamRead):
    heroes: list[HeroRead] = []


# End Hero and Team link models ###


# Define FastAPI application ###
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


# End Define FastAPI application ###


# Hero CRUD ###
@app.post("/heroes/", response_model=HeroRead)
def create_hero(
    session: Annotated[Session, Depends(get_session)],
    hero: Annotated[HeroCreate, Body()],
):
    db_hero = Hero.from_orm(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@app.get("/heroes/", response_model=list[HeroRead])
def read_heroes(
    session: Annotated[Session, Depends(get_session)],
    offset: Annotated[int, Query()] = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


@app.get("/heroes/{hero_id}", response_model=HeroReadWithTeam)
def read_hero(
    session: Annotated[Session, Depends(get_session)], hero_id: Annotated[int, Path()]
):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@app.patch("/heroes/{hero_id}", response_model=HeroRead)
def update_hero(
    session: Annotated[Session, Depends(get_session)],
    hero_id: Annotated[int, Path()],
    hero: Annotated[HeroUpdate, Body()],
):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.dict(exclude_unset=True)
    for key, value in hero_data.items():
        setattr(db_hero, key, value)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@app.delete("/heroes/{hero_id}")
def delete_hero(
    session: Annotated[Session, Depends(get_session)], hero_id: Annotated[int, Path()]
):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}


# End Hero CRUD ###


# Team CRUD ###
@app.post("/teams/", response_model=TeamRead)
def create_team(
    session: Annotated[Session, Depends(get_session)],
    team: Annotated[TeamCreate, Body()],
):
    db_team = Team.from_orm(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@app.get("/teams/", response_model=list[TeamRead])
def read_teams(
    session: Annotated[Session, Depends(get_session)],
    offset: Annotated[int, Query()] = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    teams = session.exec(select(Team).offset(offset).limit(limit)).all()
    return teams


@app.get("/teams/{team_id}", response_model=TeamReadWithHeroes)
def read_team(
    session: Annotated[Session, Depends(get_session)], team_id: Annotated[int, Path()]
):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@app.patch("/teams/{team_id}", response_model=TeamRead)
def update_team(
    session: Annotated[Session, Depends(get_session)],
    team_id: Annotated[int, Path()],
    team: Annotated[TeamUpdate, Body()],
):
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    team_data = team.dict(exclude_unset=True)
    for key, value in team_data.items():
        setattr(db_team, key, value)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@app.delete("/teams/{team_id}")
def delete_team(
    session: Annotated[Session, Depends(get_session)], team_id: Annotated[int, Path()]
):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    session.delete(team)
    session.commit()
    return {"ok": True}


# End Team CRUD ###

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.dependencies.database import create_db_and_tables
from app.routers.heroes import hero_router
from app.routers.teams import team_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown


app = FastAPI(lifespan=lifespan)

app.include_router(hero_router)
app.include_router(team_router)

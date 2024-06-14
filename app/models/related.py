from typing import Optional

from app.models.team import TeamPublic
from app.models.hero import HeroPublic


class HeroPublicWithTeam(HeroPublic):
    team: Optional[TeamPublic] = None


class TeamPublicWithHeroes(TeamPublic):
    heroes: list[HeroPublic] | None = None

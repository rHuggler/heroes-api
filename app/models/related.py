from typing import Optional

from .team import TeamPublic
from .hero import HeroPublic


class HeroPublicWithTeam(HeroPublic):
    team: Optional[TeamPublic] = None


class TeamPublicWithHeroes(TeamPublic):
    heroes: list[HeroPublic] | None = None

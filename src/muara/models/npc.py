from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from muara.models.world_clock import Shift


class NPCSchedule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shift: Shift
    location: str


class NPCEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    traits: list[str] = Field(default_factory=list)
    default_location: str
    schedules: list[NPCSchedule] = Field(default_factory=list)

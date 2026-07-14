from __future__ import annotations

import re
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SaveState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = 1
    save_id: str
    player_name: str | None = None
    current_chapter: str
    current_scene: str
    completed: bool = False
    flags: dict[str, bool | str | int] = Field(default_factory=dict)
    flag_sets: dict[str, list[str]] = Field(default_factory=dict)
    chapters_completed: list[str] = Field(default_factory=list)
    endings_achieved: list[str] = Field(default_factory=list)
    last_saved: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    playthrough_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("save_id")
    @classmethod
    def save_id_must_be_safe(cls, save_id: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", save_id):
            raise ValueError(
                f"save_id {save_id!r} tidak valid — hanya boleh huruf, angka, "
                "underscore, atau hyphen. Tidak boleh mengandung path separator."
            )
        return save_id

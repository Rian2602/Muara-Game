from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator


class FlagAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    value: bool | int | str

    @classmethod
    def from_raw_string(cls, raw: str) -> "FlagAssignment":
        if ":" not in raw:
            raise ValueError(
                f"set_flags entry tidak valid, harus format 'key: value': {raw!r}"
            )
        key_part, _, value_part = raw.partition(":")
        key = key_part.strip()
        value_str = value_part.strip()

        if not key:
            raise ValueError(f"set_flags entry punya key kosong: {raw!r}")

        lowered = value_str.lower()
        if lowered == "true":
            value: bool | int | str = True
        elif lowered == "false":
            value = False
        else:
            try:
                value = int(value_str)
            except ValueError:
                value = value_str

        return cls(key=key, value=value)


class ChoiceOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    next: str
    set_flags: list[str] = Field(default_factory=list)
    _parsed_flags_cache: list[FlagAssignment] = PrivateAttr(default_factory=list)

    def model_post_init(self, _context: object) -> None:
        object.__setattr__(
            self, "_parsed_flags_cache",
            [FlagAssignment.from_raw_string(raw) for raw in self.set_flags],
        )

    @property
    def parsed_flags(self) -> list[FlagAssignment]:
        return self._parsed_flags_cache


class TextVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition: str
    text: str
    default: bool = False


class Choice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str
    options: list[ChoiceOption]

    @field_validator("options")
    @classmethod
    def must_have_at_least_two_options(
        cls, options: list[ChoiceOption]
    ) -> list[ChoiceOption]:
        if len(options) < 2:
            raise ValueError(
                "Choice harus punya minimal 2 options — kalau cuma 1 opsi, "
                "itu bukan pilihan, hapus 'choice' dan pakai 'next_chapter' "
                "langsung di scene."
            )
        return options

    @field_validator("options")
    @classmethod
    def option_ids_must_be_unique(
        cls, options: list[ChoiceOption]
    ) -> list[ChoiceOption]:
        ids = [opt.id for opt in options]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Option id duplikat di dalam satu choice: {ids}")
        return options


class Scene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    text_variants: list[TextVariant] | None = None
    choice: Choice | None = None
    next_chapter: str | None = None
    next_ending: str | None = None

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, text: str) -> str:
        if not text.strip():
            raise ValueError("Scene.text tidak boleh kosong/hanya whitespace")
        return text

    @model_validator(mode="after")
    def text_and_variants_mutually_exclusive(self) -> "Scene":
        if self.text_variants and self.text.strip():
            has_default = any(v.default for v in self.text_variants)
            if not has_default:
                raise ValueError(
                    f"Scene {self.id!r} punya 'text_variants' tanpa variant "
                    "'default: true' — harus ada fallback jika tidak ada "
                    "condition yang cocok."
                )
        return self

    @model_validator(mode="after")
    def terminal_fields_mutually_exclusive(self) -> "Scene":
        terminals = [
            self.choice is not None,
            self.next_chapter is not None,
            self.next_ending is not None,
        ]
        if sum(terminals) > 1:
            raise ValueError(
                f"Scene {self.id!r} punya lebih dari satu terminal "
                "(choice/next_chapter/next_ending) — pilih salah satu."
            )
        return self


class Chapter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    location: str
    date: str
    time: str
    scenes: list[Scene]
    _scene_index: dict[str, Scene] = PrivateAttr(default_factory=dict)
    _scene_order: dict[str, int] = PrivateAttr(default_factory=dict)

    @field_validator("scenes")
    @classmethod
    def must_have_at_least_one_scene(cls, scenes: list[Scene]) -> list[Scene]:
        if len(scenes) == 0:
            raise ValueError("Chapter harus punya minimal 1 scene")
        return scenes

    @field_validator("scenes")
    @classmethod
    def scene_ids_must_be_unique(cls, scenes: list[Scene]) -> list[Scene]:
        ids = [scene.id for scene in scenes]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Scene id duplikat di dalam satu bab: {ids}")
        return scenes

    @model_validator(mode="after")
    def validate_scene_references(self) -> "Chapter":
        scene_ids = {scene.id for scene in self.scenes}
        for scene in self.scenes:
            if scene.choice is not None:
                for option in scene.choice.options:
                    if option.next not in scene_ids:
                        raise ValueError(
                            f"ChoiceOption.next {option.next!r} di scene "
                            f"{scene.id!r} tidak ada di bab {self.id!r} — "
                            f"scene id yang tersedia: {sorted(scene_ids)}"
                        )
        return self

    def model_post_init(self, _context: object) -> None:
        object.__setattr__(
            self, "_scene_index", {scene.id: scene for scene in self.scenes}
        )
        object.__setattr__(
            self, "_scene_order", {scene.id: i for i, scene in enumerate(self.scenes)}
        )

    def get_scene(self, scene_id: str) -> Scene:
        try:
            return self._scene_index[scene_id]
        except KeyError:
            raise KeyError(
                f"Scene id {scene_id!r} tidak ditemukan di bab {self.id!r}"
            )

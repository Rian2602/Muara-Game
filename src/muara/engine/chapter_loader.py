from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from muara.models.chapter import Chapter, ConditionOperator, FlagCondition


class ChapterLoadError(Exception):
    """Raised when a chapter YAML file cannot be read, parsed, or validated."""


def _check_condition_type_sanity(
    condition: FlagCondition, chapter_id: str, scene_id: str
) -> None:
    """Validasi statis: operator relasional tidak masuk akal untuk flag boolean."""
    relational = {
        ConditionOperator.GT, ConditionOperator.GTE,
        ConditionOperator.LT, ConditionOperator.LTE,
    }
    if condition.operator in relational and isinstance(condition.value, bool):
        raise ChapterLoadError(
            f"Bab {chapter_id!r} scene {scene_id!r}: operator "
            f"{condition.operator.value!r} tidak valid untuk flag boolean "
            f"({condition.flag!r}). Gunakan == atau != untuk boolean."
        )


def _validate_conditions_statically(chapter: Chapter) -> None:
    """Validasi semua kondisi di chapter saat load (tidak butuh flags aktual)."""
    for scene in chapter.scenes:
        for condition in scene.requires:
            _check_condition_type_sanity(condition, chapter.id, scene.id)
        if scene.choice:
            for option in scene.choice.options:
                for condition in option.visible_if:
                    _check_condition_type_sanity(condition, chapter.id, scene.id)


def load_chapter(path: str | Path) -> Chapter:
    file_path = Path(path)

    if not file_path.exists():
        raise ChapterLoadError(f"File bab tidak ditemukan: {file_path}")

    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ChapterLoadError(f"Gagal membaca file bab {file_path}: {exc}") from exc

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ChapterLoadError(f"YAML tidak valid di {file_path}: {exc}") from exc

    if data is None:
        raise ChapterLoadError(f"File bab kosong: {file_path}")

    try:
        chapter = Chapter.model_validate(data)
    except ValidationError as exc:
        raise ChapterLoadError(
            f"Skema bab tidak valid di {file_path}:\n{exc}"
        ) from exc

    _validate_conditions_statically(chapter)
    return chapter


def load_manifest(content_dir: Path | str) -> list[str]:
    file_path = Path(content_dir) / "manifest.yaml"

    if not file_path.exists():
        raise ChapterLoadError(f"File manifest tidak ditemukan: {file_path}")

    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ChapterLoadError(f"Gagal membaca manifest {file_path}: {exc}") from exc

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ChapterLoadError(f"YAML manifest tidak valid di {file_path}: {exc}") from exc

    if data is None or "chapters" not in data:
        raise ChapterLoadError(
            f"Manifest {file_path} harus punya key 'chapters' (boleh list kosong)"
        )

    chapters = data["chapters"]
    if not isinstance(chapters, list) or not all(
        isinstance(item, str) for item in chapters
    ):
        raise ChapterLoadError(
            f"'chapters' di manifest {file_path} harus berupa list of string"
        )

    return chapters


def load_all_chapters(chapters_dir: str | Path) -> dict[str, Chapter]:
    """Load all chapters from a directory. Utility for batch operations and testing.
    
    Note: Application code uses load_manifest() + individual load_chapter() calls.
    This function is for convenience when you need all chapters at once.
    """
    dir_path = Path(chapters_dir)
    if not dir_path.is_dir():
        raise ChapterLoadError(f"Folder bab tidak ditemukan: {dir_path}")

    chapters: dict[str, Chapter] = {}
    for yaml_file in sorted(dir_path.glob("*.yaml")):
        chapter = load_chapter(yaml_file)
        if chapter.id in chapters:
            raise ChapterLoadError(
                f"Chapter id {chapter.id!r} muncul di lebih dari satu file "
                f"(duplikat terakhir ditemukan di {yaml_file})"
            )
        chapters[chapter.id] = chapter

    return chapters

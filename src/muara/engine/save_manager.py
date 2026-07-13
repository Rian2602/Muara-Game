from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from muara.models.save_state import SaveState


class SaveLoadError(Exception):
    """Raised when a save file cannot be read, written, or validated."""


def _save_path(saves_dir: str | Path, save_id: str) -> Path:
    return Path(saves_dir) / f"{save_id}.json"


def save(save_state: SaveState, saves_dir: str | Path) -> Path:
    saves_path = Path(saves_dir)
    saves_path.mkdir(parents=True, exist_ok=True)

    file_path = _save_path(saves_path, save_state.save_id)
    tmp_path = file_path.with_suffix(".json.tmp")
    try:
        tmp_path.write_text(
            save_state.model_dump_json(indent=2), encoding="utf-8"
        )
        tmp_path.replace(file_path)
    except OSError as exc:
        raise SaveLoadError(f"Gagal menulis save file {file_path}: {exc}") from exc
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

    return file_path


def load(save_id: str, saves_dir: str | Path) -> SaveState:
    file_path = _save_path(saves_dir, save_id)

    if not file_path.exists():
        raise SaveLoadError(f"Save file tidak ditemukan: {file_path}")

    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SaveLoadError(f"Gagal membaca save file {file_path}: {exc}") from exc

    try:
        return SaveState.model_validate_json(raw_text)
    except ValidationError as exc:
        raise SaveLoadError(
            f"Save file {file_path} korup atau tidak kompatibel: {exc}"
        ) from exc


def list_saves(saves_dir: str | Path) -> list[str]:
    saves_path = Path(saves_dir)
    if not saves_path.is_dir():
        return []
    return sorted(f.stem for f in saves_path.glob("*.json"))

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ValidationError

from muara.models.save_state import SaveState


class SaveLoadError(Exception):
    """Raised when a save file cannot be read, written, or validated."""


class SaveSlotInfo(BaseModel):
    """Metadata for a save slot, used for display in slot selection UI."""
    save_id: str
    player_name: str | None = None
    current_chapter: str
    current_scene: str
    completed: bool = False
    last_saved: str
    playthrough_start: str
    endings_achieved: list[str] = []
    key_flags: list[str] = []


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


def list_save_slots(saves_dir: str | Path) -> list[SaveSlotInfo]:
    """List all save slots with metadata for display in UI."""
    slots = []
    for save_id in list_saves(saves_dir):
        try:
            save_state = load(save_id, saves_dir)
            key_flags = []
            if save_state.flags.get("berbicara_dengan_jaya"):
                key_flags.append("Jaya")
            if save_state.flags.get("melihat_anomali"):
                key_flags.append("Anomali")
            if save_state.flags.get("melapor"):
                key_flags.append("Lapor")
            if save_state.flags.get("percaya_jaya"):
                key_flags.append("Percaya Jaya")
            if save_state.flags.get("konfrontasi_berhasil"):
                key_flags.append("Konfrontasi")
            
            slot = SaveSlotInfo(
                save_id=save_id,
                player_name=save_state.player_name,
                current_chapter=save_state.current_chapter,
                current_scene=save_state.current_scene,
                completed=save_state.completed,
                last_saved=save_state.last_saved.strftime("%d %b %Y, %H:%M"),
                playthrough_start=save_state.playthrough_start.strftime("%d %b %Y, %H:%M"),
                endings_achieved=save_state.endings_achieved,
                key_flags=key_flags,
            )
            slots.append(slot)
        except SaveLoadError:
            continue
    return slots


def delete_save(save_id: str, saves_dir: str | Path) -> None:
    """Delete a save file."""
    file_path = _save_path(saves_dir, save_id)
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError as exc:
            raise SaveLoadError(f"Gagal menghapus save file {file_path}: {exc}") from exc


def rename_save(old_id: str, new_id: str, saves_dir: str | Path) -> None:
    """Rename a save file."""
    old_path = _save_path(saves_dir, old_id)
    new_path = _save_path(saves_dir, new_id)
    if not old_path.exists():
        raise SaveLoadError(f"Save file tidak ditemukan: {old_path}")
    if new_path.exists():
        raise SaveLoadError(f"Save file sudah ada: {new_path}")
    try:
        old_path.rename(new_path)
    except OSError as exc:
        raise SaveLoadError(f"Gagal rename save file: {exc}") from exc

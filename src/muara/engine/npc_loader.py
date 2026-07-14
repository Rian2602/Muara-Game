from pathlib import Path
import yaml
from pydantic import ValidationError

from muara.models.npc import NPCEntity


class NPCLoadError(Exception):
    """Dibangkitkan saat gagal memuat atau memvalidasi file npcs.yaml."""


def load_npcs(path: Path | str) -> list[NPCEntity]:
    path = Path(path)
    if not path.is_file():
        raise NPCLoadError(f"File NPC tidak ditemukan: {path}")

    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise NPCLoadError(f"Error parse YAML pada {path}: {e}") from e

    if not isinstance(data, dict) or "npcs" not in data or not isinstance(data["npcs"], list):
        raise NPCLoadError(f"Skema YAML tidak valid pada {path}: root harus dict dengan key 'npcs' berisi list.")

    npcs = []
    for i, npc_data in enumerate(data["npcs"]):
        try:
            npc = NPCEntity.model_validate(npc_data)
            npcs.append(npc)
        except ValidationError as e:
            raise NPCLoadError(f"Validasi NPC index {i} gagal pada {path}: {e}") from e

    return npcs

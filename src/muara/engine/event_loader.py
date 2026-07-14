from pathlib import Path
import yaml
from pydantic import ValidationError

from muara.models.world_clock import WorldEvent


class EventLoadError(Exception):
    """Dibangkitkan saat gagal memuat atau memvalidasi file events.yaml."""


def load_events(path: Path | str) -> list[WorldEvent]:
    path = Path(path)
    if not path.is_file():
        raise EventLoadError(f"File event tidak ditemukan: {path}")

    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise EventLoadError(f"Error parse YAML pada {path}: {e}") from e

    if not isinstance(data, dict) or "events" not in data or not isinstance(data["events"], list):
        raise EventLoadError(f"Skema YAML tidak valid pada {path}: root harus dict dengan key 'events' berisi list.")

    events = []
    for i, event_data in enumerate(data["events"]):
        try:
            event = WorldEvent.model_validate(event_data)
            events.append(event)
        except ValidationError as e:
            raise EventLoadError(f"Validasi event index {i} gagal pada {path}: {e}") from e

    return events

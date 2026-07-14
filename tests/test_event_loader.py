import pytest
from pathlib import Path

from muara.engine.event_loader import load_events, EventLoadError
from muara.models.world_clock import Shift


def test_load_events_valid(tmp_path: Path):
    yaml_content = """
events:
  - id: "test_event"
    trigger:
      day: 2
      shift: "pagi"
    set_flags:
      - "memasuki_hari_kedua: true"
    repeatable: false
"""
    file_path = tmp_path / "events.yaml"
    file_path.write_text(yaml_content)
    
    events = load_events(file_path)
    assert len(events) == 1
    assert events[0].id == "test_event"
    assert events[0].trigger.day == 2
    assert events[0].trigger.shift == Shift.PAGI
    assert events[0].set_flags == ["memasuki_hari_kedua: true"]
    assert events[0].repeatable is False


def test_load_events_file_not_found(tmp_path: Path):
    with pytest.raises(EventLoadError, match="File event tidak ditemukan"):
        load_events(tmp_path / "nonexistent.yaml")


def test_load_events_invalid_yaml(tmp_path: Path):
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text("invalid: yaml: [")
    
    with pytest.raises(EventLoadError, match="Error parse YAML"):
        load_events(file_path)


def test_load_events_invalid_schema_root(tmp_path: Path):
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text("not_events: []")
    
    with pytest.raises(EventLoadError, match="Skema YAML tidak valid"):
        load_events(file_path)


def test_load_events_validation_error(tmp_path: Path):
    yaml_content = """
events:
  - id: "test_event"
    # trigger is missing
    extra_field: "forbidden"
"""
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text(yaml_content)
    
    with pytest.raises(EventLoadError, match="Validasi event index 0 gagal"):
        load_events(file_path)

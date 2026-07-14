import pytest
from pathlib import Path

from muara.engine.npc_loader import load_npcs, NPCLoadError
from muara.models.world_clock import Shift


def test_load_npcs_valid(tmp_path: Path):
    yaml_content = """
npcs:
  - id: "sutisna"
    name: "Sutisna"
    traits: ["tegas"]
    default_location: "gudang_utama"
    schedules:
      - shift: "malam"
        location: "pos_jaga"
"""
    file_path = tmp_path / "npcs.yaml"
    file_path.write_text(yaml_content)
    
    npcs = load_npcs(file_path)
    assert len(npcs) == 1
    assert npcs[0].id == "sutisna"
    assert npcs[0].name == "Sutisna"
    assert npcs[0].traits == ["tegas"]
    assert npcs[0].default_location == "gudang_utama"
    assert len(npcs[0].schedules) == 1
    assert npcs[0].schedules[0].shift == Shift.MALAM
    assert npcs[0].schedules[0].location == "pos_jaga"


def test_load_npcs_file_not_found(tmp_path: Path):
    with pytest.raises(NPCLoadError, match="File NPC tidak ditemukan"):
        load_npcs(tmp_path / "nonexistent.yaml")


def test_load_npcs_invalid_yaml(tmp_path: Path):
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text("invalid: yaml: [")
    
    with pytest.raises(NPCLoadError, match="Error parse YAML"):
        load_npcs(file_path)


def test_load_npcs_invalid_schema_root(tmp_path: Path):
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text("not_npcs: []")
    
    with pytest.raises(NPCLoadError, match="Skema YAML tidak valid"):
        load_npcs(file_path)


def test_load_npcs_validation_error(tmp_path: Path):
    yaml_content = """
npcs:
  - id: "sutisna"
    # missing required fields
"""
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text(yaml_content)
    
    with pytest.raises(NPCLoadError, match="Validasi NPC index 0 gagal"):
        load_npcs(file_path)

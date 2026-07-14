"""Tests for new features: multi-slot saves, typewriter, scene hooks."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch

from muara.engine.save_manager import (
    save,
    load,
    list_saves,
    list_save_slots,
    delete_save,
    rename_save,
    SaveLoadError,
    SaveSlotInfo,
)
from muara.engine.state import GameState
from muara.engine.chapter_runner import ChapterRunner, ChapterRunError
from muara.models.save_state import SaveState
from muara.models.chapter import Chapter, Scene


class TestMultiSlotSaves:
    """Tests for multi-slot save system."""

    def test_list_save_slots_empty_dir(self, tmp_path: Path):
        """list_save_slots returns empty list when no saves exist."""
        slots = list_save_slots(tmp_path)
        assert slots == []

    def test_list_save_slots_with_saves(self, tmp_path: Path):
        """list_save_slots returns metadata for each save."""
        # Create two saves
        save1 = SaveState(
            save_id="slot1",
            current_chapter="01_pembukaan",
            current_scene="scene_1",
            flags={"melihat_anomali": True},
        )
        save2 = SaveState(
            save_id="slot2",
            current_chapter="02_gejala",
            current_scene="scene_2",
            flags={"berbicara_dengan_jaya": True},
        )
        save(save1, tmp_path)
        save(save2, tmp_path)

        slots = list_save_slots(tmp_path)
        assert len(slots) == 2
        assert slots[0].save_id == "slot1"
        assert slots[0].key_flags == ["Anomali"]
        assert slots[1].save_id == "slot2"
        assert slots[1].key_flags == ["Jaya"]

    def test_delete_save(self, tmp_path: Path):
        """delete_save removes the save file."""
        save_state = SaveState(
            save_id="to_delete",
            current_chapter="01_pembukaan",
            current_scene="scene_1",
        )
        save(save_state, tmp_path)
        assert len(list_saves(tmp_path)) == 1

        delete_save("to_delete", tmp_path)
        assert len(list_saves(tmp_path)) == 0

    def test_delete_save_nonexistent(self, tmp_path: Path):
        """delete_save on nonexistent save does not raise."""
        delete_save("nonexistent", tmp_path)  # Should not raise

    def test_rename_save(self, tmp_path: Path):
        """rename_save changes the save file name."""
        save_state = SaveState(
            save_id="old_name",
            current_chapter="01_pembukaan",
            current_scene="scene_1",
        )
        save(save_state, tmp_path)

        rename_save("old_name", "new_name", tmp_path)
        assert "new_name.json" in [f.name for f in tmp_path.glob("*.json")]
        assert "old_name.json" not in [f.name for f in tmp_path.glob("*.json")]

    def test_rename_save_nonexistent(self, tmp_path: Path):
        """rename_save on nonexistent save raises error."""
        with pytest.raises(SaveLoadError):
            rename_save("nonexistent", "new_name", tmp_path)

    def test_rename_save_target_exists(self, tmp_path: Path):
        """rename_save to existing name raises error."""
        save1 = SaveState(
            save_id="first",
            current_chapter="01_pembukaan",
            current_scene="scene_1",
        )
        save2 = SaveState(
            save_id="second",
            current_chapter="02_gejala",
            current_scene="scene_2",
        )
        save(save1, tmp_path)
        save(save2, tmp_path)

        with pytest.raises(SaveLoadError):
            rename_save("first", "second", tmp_path)


class TestSceneHooks:
    """Tests for scene transition hooks (on_enter/on_exit)."""

    def test_on_enter_sets_flag(self):
        """on_enter hook sets flag when entering scene."""
        chapter = Chapter(
            id="test_chapter",
            title="Test Chapter",
            location="Test Location",
            date="01 Jan 1900",
            time="12.00",
            scenes=[
                Scene(id="scene_1", text="First scene", on_enter=["entered_scene: true"], next_chapter="test_chapter"),
                Scene(id="scene_2", text="Second scene", next_chapter="test_chapter"),
            ],
        )
        state = GameState.new_playthrough("test", "test_chapter", "scene_1")
        renderer = _make_dummy_renderer()
        
        runner = ChapterRunner(chapter, state, renderer, input_fn=lambda _: "")
        # Run will exit at next_chapter
        try:
            runner.run("scene_1")
        except:
            pass
        
        assert state.get_flag("entered_scene") is True

    def test_on_exit_sets_flag(self):
        """on_exit hook sets flag when exiting scene."""
        chapter = Chapter(
            id="test_chapter",
            title="Test Chapter",
            location="Test Location",
            date="01 Jan 1900",
            time="12.00",
            scenes=[
                Scene(id="scene_1", text="First scene", on_exit=["exited_scene: true"], next_chapter="test_chapter"),
                Scene(id="scene_2", text="Second scene", next_chapter="test_chapter"),
            ],
        )
        state = GameState.new_playthrough("test", "test_chapter", "scene_1")
        renderer = _make_dummy_renderer()
        
        runner = ChapterRunner(chapter, state, renderer, input_fn=lambda _: "")
        try:
            runner.run("scene_1")
        except:
            pass
        
        assert state.get_flag("exited_scene") is True

    def test_on_enter_increment_counter(self):
        """on_enter hook can increment a counter."""
        chapter = Chapter(
            id="test_chapter",
            title="Test Chapter",
            location="Test Location",
            date="01 Jan 1900",
            time="12.00",
            scenes=[
                Scene(id="scene_1", text="First scene", on_enter=["increment(visit_count)"], next_chapter="test_chapter"),
            ],
        )
        state = GameState.new_playthrough("test", "test_chapter", "scene_1")
        renderer = _make_dummy_renderer()
        
        runner = ChapterRunner(chapter, state, renderer, input_fn=lambda _: "")
        try:
            runner.run("scene_1")
        except:
            pass
        
        assert state.get_flag("visit_count") == 1


class TestTypewriterRenderer:
    """Tests for typewriter effect in CLIRenderer."""

    def test_typewriter_disabled_by_default(self):
        """CLIRenderer has typewriter disabled by default."""
        from muara.engine.render_cli import CLIRenderer
        from rich.console import Console
        
        console = Console()
        renderer = CLIRenderer(console)
        assert renderer.typewriter is False

    def test_typewriter_can_be_enabled(self):
        """CLIRenderer can be created with typewriter enabled."""
        from muara.engine.render_cli import CLIRenderer
        from rich.console import Console
        
        console = Console()
        renderer = CLIRenderer(console, typewriter=True, typewriter_delay=0.05)
        assert renderer.typewriter is True
        assert renderer.typewriter_delay == 0.05


def _make_dummy_renderer():
    """Create a dummy renderer for testing."""
    from muara.engine.render_cli import CLIRenderer
    from rich.console import Console
    
    console = Console()
    return CLIRenderer(console)
"""Tests for src/muara/main.py — orchestration entry point."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import pytest

from muara.main import (
    _format_elapsed,
    _find_chapter_path_by_id,
    _prompt_save_slot_selection,
    _resolve_chapter_sequence,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _dt(day: int = 1, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    """Create a UTC datetime for easy timedelta arithmetic."""
    return datetime(2026, 7, 15, hour, minute, second, tzinfo=timezone.utc)


class FakeRenderer:
    """Minimal Renderer stub that records rendered lines."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def render_line(self, text: str = "") -> None:
        self.lines.append(str(text))

    def render_chapter_header(self, **kwargs) -> None:
        pass

    def render_scene_text(self, text: str) -> None:
        self.lines.append(text)

    def render_choice_prompt(self, prompt: str, options: list) -> None:
        pass

    def render_continue_prompt(self) -> None:
        pass

    def render_error(self, message: str) -> None:
        self.lines.append(f"ERROR: {message}")


def _make_chapter_yaml(chapter_id: str, title: str = "Test Chapter", **extra) -> str:
    """Return a minimal valid chapter YAML string."""
    return f"""id: "{chapter_id}"
title: "{title}"
location: "Test Location"
date: "15 Juli 2026"
time: "10.00"
scenes:
  - id: "scene_1"
    text: "Aku berada di sini."
    next_chapter: "__END__"
"""


def _write_save(saves_dir: Path, save_id: str, **overrides) -> Path:
    """Write a minimal save file for testing."""
    import json

    save_data = {
        "version": 3,
        "save_id": save_id,
        "player_name": None,
        "current_chapter": overrides.get("current_chapter", "01_test"),
        "current_scene": overrides.get("current_scene", "scene_1"),
        "chapters_completed": overrides.get("chapters_completed", []),
        "flags": overrides.get("flags", {}),
        "flag_sets": overrides.get("flag_sets", {}),
        "endings_achieved": overrides.get("endings_achieved", []),
        "completed": overrides.get("completed", False),
        "last_saved": "2026-07-15T10:00:00+00:00",
        "playthrough_start": "2026-07-15T10:00:00+00:00",
        "world_clock": {
            "day": 1,
            "shift": "pagi",
        },
        "reputations": {},
    }
    save_path = saves_dir / f"{save_id}.json"
    save_path.write_text(json.dumps(save_data))
    return save_path


# ── _format_elapsed tests ───────────────────────────────────────────

class TestFormatElapsed:
    def test_minutes_only(self) -> None:
        start = _dt(hour=0, minute=0, second=0)
        end = _dt(hour=0, minute=5, second=30)
        assert _format_elapsed(start, end) == "05:30"

    def test_hours_minutes_seconds(self) -> None:
        start = _dt(hour=1, minute=0, second=0)
        end = _dt(hour=3, minute=15, second=45)
        assert _format_elapsed(start, end) == "02:15:45"

    def test_zero_duration(self) -> None:
        now = _dt(hour=12, minute=0, second=0)
        assert _format_elapsed(now, now) == "00:00"

    def test_large_duration(self) -> None:
        start = _dt(hour=0, minute=0, second=0)
        end = _dt(hour=10, minute=0, second=0)
        assert _format_elapsed(start, end) == "10:00:00"


# ── _prompt_save_slot_selection tests ────────────────────────────────

class TestPromptSaveSlotSelection:
    def test_no_saves_returns_new(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_saves = main_mod.SAVES_DIR
        main_mod.SAVES_DIR = tmp_path
        try:
            renderer = FakeRenderer()
            action, state = _prompt_save_slot_selection(renderer, ["01_test"])
            assert action == "new"
            assert state is None
        finally:
            main_mod.SAVES_DIR = old_saves

    def test_user_types_b_returns_new(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_saves = main_mod.SAVES_DIR
        main_mod.SAVES_DIR = tmp_path
        try:
            _write_save(tmp_path, "save_1")
            renderer = FakeRenderer()
            inputs = iter(["b"])
            action, state = _prompt_save_slot_selection(
                renderer, ["01_test"], input_fn=lambda _: next(inputs)
            )
            assert action == "new"
            assert state is None
        finally:
            main_mod.SAVES_DIR = old_saves

    def test_user_types_baru_returns_new(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_saves = main_mod.SAVES_DIR
        main_mod.SAVES_DIR = tmp_path
        try:
            _write_save(tmp_path, "save_1")
            renderer = FakeRenderer()
            inputs = iter(["baru"])
            action, state = _prompt_save_slot_selection(
                renderer, ["01_test"], input_fn=lambda _: next(inputs)
            )
            assert action == "new"
            assert state is None
        finally:
            main_mod.SAVES_DIR = old_saves

    def test_user_types_new_returns_new(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_saves = main_mod.SAVES_DIR
        main_mod.SAVES_DIR = tmp_path
        try:
            _write_save(tmp_path, "save_1")
            renderer = FakeRenderer()
            inputs = iter(["new"])
            action, state = _prompt_save_slot_selection(
                renderer, ["01_test"], input_fn=lambda _: next(inputs)
            )
            assert action == "new"
            assert state is None
        finally:
            main_mod.SAVES_DIR = old_saves

    def test_valid_selection_loads_save(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_saves = main_mod.SAVES_DIR
        main_mod.SAVES_DIR = tmp_path
        try:
            _write_save(tmp_path, "save_1", current_chapter="01_test")
            renderer = FakeRenderer()
            inputs = iter(["1"])
            action, state = _prompt_save_slot_selection(
                renderer, ["01_test"], input_fn=lambda _: next(inputs)
            )
            assert action == "continue"
            assert state is not None
            assert state.save_state.save_id == "save_1"
        finally:
            main_mod.SAVES_DIR = old_saves

    def test_out_of_range_loops(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_saves = main_mod.SAVES_DIR
        main_mod.SAVES_DIR = tmp_path
        try:
            _write_save(tmp_path, "save_1")
            renderer = FakeRenderer()
            # First input: out of range, second input: valid
            inputs = iter(["99", "1"])
            action, state = _prompt_save_slot_selection(
                renderer, ["01_test"], input_fn=lambda _: next(inputs)
            )
            assert action == "continue"
            assert state is not None
            # Should have rendered error about invalid answer
            assert any("tidak valid" in line.lower() or "invalid" in line.lower() for line in renderer.lines)
        finally:
            main_mod.SAVES_DIR = old_saves

    def test_non_digit_non_b_loops(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_saves = main_mod.SAVES_DIR
        main_mod.SAVES_DIR = tmp_path
        try:
            _write_save(tmp_path, "save_1")
            renderer = FakeRenderer()
            # First input: random text, second: valid
            inputs = iter(["xyz", "1"])
            action, state = _prompt_save_slot_selection(
                renderer, ["01_test"], input_fn=lambda _: next(inputs)
            )
            assert action == "continue"
        finally:
            main_mod.SAVES_DIR = old_saves


# ── _resolve_chapter_sequence tests ─────────────────────────────────

class TestResolveChapterSequence:
    def test_normal_manifest_returns_ids(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_content = main_mod.CONTENT_DIR
        main_mod.CONTENT_DIR = tmp_path
        try:
            # Write manifest
            (tmp_path / "manifest.yaml").write_text(
                'chapters:\n  - "01_alpha"\n  - "02_beta"\n'
            )
            renderer = FakeRenderer()
            result = _resolve_chapter_sequence(renderer)
            assert result == ["01_alpha", "02_beta"]
        finally:
            main_mod.CONTENT_DIR = old_content

    def test_empty_manifest_fallback_scans_chapters(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_content = main_mod.CONTENT_DIR
        old_chapters = main_mod.CHAPTERS_DIR
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        main_mod.CONTENT_DIR = tmp_path
        main_mod.CHAPTERS_DIR = chapters_dir
        try:
            # Write empty manifest in CONTENT_DIR
            (tmp_path / "manifest.yaml").write_text("chapters: []\n")
            # Write one chapter YAML in CHAPTERS_DIR
            (chapters_dir / "01_alpha.yaml").write_text(_make_chapter_yaml("01_alpha"))
            renderer = FakeRenderer()
            result = _resolve_chapter_sequence(renderer)
            assert result == ["01_alpha"]
            # Should have rendered fallback warning
            assert any("fallback" in line.lower() for line in renderer.lines)
        finally:
            main_mod.CONTENT_DIR = old_content
            main_mod.CHAPTERS_DIR = old_chapters

    def test_empty_directory_exits(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_content = main_mod.CONTENT_DIR
        old_chapters = main_mod.CHAPTERS_DIR
        main_mod.CONTENT_DIR = tmp_path
        main_mod.CHAPTERS_DIR = tmp_path
        try:
            # Write empty manifest
            (tmp_path / "manifest.yaml").write_text("chapters: []\n")
            renderer = FakeRenderer()
            with pytest.raises(SystemExit):
                _resolve_chapter_sequence(renderer)
        finally:
            main_mod.CONTENT_DIR = old_content
            main_mod.CHAPTERS_DIR = old_chapters


# ── _find_chapter_path_by_id tests ──────────────────────────────────

class TestFindChapterPathById:
    def test_convention_path_found(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_chapters = main_mod.CHAPTERS_DIR
        main_mod.CHAPTERS_DIR = tmp_path
        try:
            chapter_file = tmp_path / "01_alpha.yaml"
            chapter_file.write_text(_make_chapter_yaml("01_alpha"))
            renderer = FakeRenderer()
            result = _find_chapter_path_by_id("01_alpha", renderer)
            assert result == chapter_file
        finally:
            main_mod.CHAPTERS_DIR = old_chapters

    def test_fallback_scan_found(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_chapters = main_mod.CHAPTERS_DIR
        main_mod.CHAPTERS_DIR = tmp_path
        try:
            # File name doesn't match convention (not 01_alpha.yaml)
            chapter_file = tmp_path / "custom_name.yaml"
            chapter_file.write_text(_make_chapter_yaml("01_alpha"))
            renderer = FakeRenderer()
            result = _find_chapter_path_by_id("01_alpha", renderer)
            assert result == chapter_file
        finally:
            main_mod.CHAPTERS_DIR = old_chapters

    def test_not_found_exits(self, tmp_path: Path) -> None:
        import muara.main as main_mod
        old_chapters = main_mod.CHAPTERS_DIR
        main_mod.CHAPTERS_DIR = tmp_path
        try:
            renderer = FakeRenderer()
            with pytest.raises(SystemExit):
                _find_chapter_path_by_id("nonexistent", renderer)
        finally:
            main_mod.CHAPTERS_DIR = old_chapters


# ── Integration tests for run() ─────────────────────────────────────

class TestRunIntegration:
    """End-to-end tests for the run() function using synthetic chapters."""

    def _setup_test_env(self, tmp_path: Path, chapters: list[dict], input_values: list[str]):
        """Set up test environment and run the game.

        Args:
            tmp_path: pytest tmp_path fixture
            chapters: List of dicts with keys: id, content (YAML string), next (optional)
            input_values: List of input strings to inject

        Returns:
            tuple: (renderer, input_fn, main_mod, old_c, old_ch, old_s)
        """
        import muara.main as main_mod

        # Create directory structure
        content_dir = tmp_path / "content"
        chapters_dir = content_dir / "chapters"
        chapters_dir.mkdir(parents=True)
        saves_dir = tmp_path / "saves"
        saves_dir.mkdir()

        # Write manifest
        chapter_ids = [ch["id"] for ch in chapters]
        manifest_content = "chapters:\n" + "\n".join(f'  - "{cid}"' for cid in chapter_ids) + "\n"
        (content_dir / "manifest.yaml").write_text(manifest_content)

        # Write chapter files
        for ch in chapters:
            (chapters_dir / f"{ch['id']}.yaml").write_text(ch["content"])

        # Patch module globals
        old_content = main_mod.CONTENT_DIR
        old_chapters = main_mod.CHAPTERS_DIR
        old_saves = main_mod.SAVES_DIR
        main_mod.CONTENT_DIR = content_dir
        main_mod.CHAPTERS_DIR = chapters_dir
        main_mod.SAVES_DIR = saves_dir

        renderer = FakeRenderer()
        input_iter = iter(input_values)
        input_fn = lambda _: next(input_iter)

        return renderer, input_fn, main_mod, old_content, old_chapters, old_saves

    def test_linear_flow_single_chapter(self, tmp_path: Path) -> None:
        """Single chapter with linear flow → reaches ending, save written."""
        chapter_content = """id: "01_test"
title: "Bab Test"
location: "Gudang, Batavia"
date: "15 Juli 1899"
time: "10.00"
scenes:
  - id: "scene_1"
    text: "Aku memasuki gudang."
    next_chapter: "__END__"
"""
        renderer, input_fn, main_mod, old_c, old_ch, old_s = self._setup_test_env(
            tmp_path,
            [{"id": "01_test", "content": chapter_content}],
            [],  # No input needed for linear flow
        )
        try:
            from muara.main import run
            import sys
            old_argv = sys.argv
            sys.argv = ["muara"]
            try:
                run(input_fn=input_fn)
            finally:
                sys.argv = old_argv

            # Verify save file was written
            saves = list((tmp_path / "saves").glob("*.json"))
            assert len(saves) == 1

            # Load and verify save state
            import json
            save_data = json.loads(saves[0].read_text())
            assert save_data["completed"] is True
            assert len(save_data["endings_achieved"]) == 1
        finally:
            main_mod.CONTENT_DIR = old_c
            main_mod.CHAPTERS_DIR = old_ch
            main_mod.SAVES_DIR = old_s

    def test_two_chapters_linear(self, tmp_path: Path) -> None:
        """Two chapters → reaches ending after second chapter."""
        ch1 = """id: "01_start"
title: "Awal"
location: "Gudang, Batavia"
date: "15 Juli 1899"
time: "10.00"
scenes:
  - id: "scene_1"
    text: "Aku memasuki gudang."
    next_chapter: "02_continue"
"""
        ch2 = """id: "02_continue"
title: "Lanjut"
location: "Gudang, Batavia"
date: "15 Juli 1899"
time: "11.00"
scenes:
  - id: "scene_1"
    text: "Aku keluar dari gudang."
    next_chapter: "__END__"
"""
        renderer, input_fn, main_mod, old_c, old_ch, old_s = self._setup_test_env(
            tmp_path,
            [{"id": "01_start", "content": ch1}, {"id": "02_continue", "content": ch2}],
            [],
        )
        try:
            from muara.main import run
            import sys
            old_argv = sys.argv
            sys.argv = ["muara"]
            try:
                run(input_fn=input_fn)
            finally:
                sys.argv = old_argv

            # Verify save file was written
            saves = list((tmp_path / "saves").glob("*.json"))
            assert len(saves) == 1

            import json
            save_data = json.loads(saves[0].read_text())
            assert save_data["completed"] is True
        finally:
            main_mod.CONTENT_DIR = old_c
            main_mod.CHAPTERS_DIR = old_ch
            main_mod.SAVES_DIR = old_s

    def test_branching_flow_choice_affects_ending(self, tmp_path: Path) -> None:
        """Chapter with choice → different ending based on selection."""
        ch_with_choice = """id: "01_choice"
title: "Pilihan"
location: "Gudang, Batavia"
date: "15 Juli 1899"
time: "10.00"
scenes:
  - id: "scene_1"
    text: "Aku berdiri di persimpangan."
    choice:
      prompt: "Ke mana?"
      options:
        - id: "option_a"
          label: "Ke kiri"
          next: "scene_left"
          set_flags:
            - "went_left: true"
        - id: "option_b"
          label: "Ke kanan"
          next: "scene_right"
          set_flags:
            - "went_left: false"
  - id: "scene_left"
    text: "Aku ke kiri."
    next_chapter: "__END__"
  - id: "scene_right"
    text: "Aku ke kanan."
    next_chapter: "__END__"
"""
        renderer, input_fn, main_mod, old_c, old_ch, old_s = self._setup_test_env(
            tmp_path,
            [{"id": "01_choice", "content": ch_with_choice}],
            ["1"],  # Select option 1 (ke kiri)
        )
        try:
            from muara.main import run
            import sys
            old_argv = sys.argv
            sys.argv = ["muara"]
            try:
                run(input_fn=input_fn)
            finally:
                sys.argv = old_argv

            # Verify save file
            saves = list((tmp_path / "saves").glob("*.json"))
            assert len(saves) == 1

            import json
            save_data = json.loads(saves[0].read_text())
            assert save_data["completed"] is True
            # Verify flag was set
            assert save_data["flags"].get("went_left") is True
        finally:
            main_mod.CONTENT_DIR = old_c
            main_mod.CHAPTERS_DIR = old_ch
            main_mod.SAVES_DIR = old_s

    def test_ending_prefix_triggers_ending(self, tmp_path: Path) -> None:
        """Chapter with next_ending → correct ending ID recorded."""
        chapter_content = """id: "01_ending"
title: "Bab Ending"
location: "Gudang, Batavia"
date: "15 Juli 1899"
time: "10.00"
scenes:
  - id: "scene_1"
    text: "Aku menemukan jalan keluar."
    next_ending: "pembebasan"
"""
        renderer, input_fn, main_mod, old_c, old_ch, old_s = self._setup_test_env(
            tmp_path,
            [{"id": "01_ending", "content": chapter_content}],
            [],
        )
        try:
            from muara.main import run
            import sys
            old_argv = sys.argv
            sys.argv = ["muara"]
            try:
                run(input_fn=input_fn)
            finally:
                sys.argv = old_argv

            saves = list((tmp_path / "saves").glob("*.json"))
            assert len(saves) == 1

            import json
            save_data = json.loads(saves[0].read_text())
            assert save_data["completed"] is True
            assert "pembebasan" in save_data["endings_achieved"]
        finally:
            main_mod.CONTENT_DIR = old_c
            main_mod.CHAPTERS_DIR = old_ch
            main_mod.SAVES_DIR = old_s

    def test_corrupted_save_loops(self, tmp_path: Path) -> None:
        """Corrupted save file → catches SaveLoadError, asks again."""
        import muara.main as main_mod
        old_saves = main_mod.SAVES_DIR
        main_mod.SAVES_DIR = tmp_path
        try:
            # Write a corrupted save file
            (tmp_path / "bad_save.json").write_text("NOT VALID JSON{{{")
            renderer = FakeRenderer()
            # First: corrupted save, second: new game
            inputs = iter(["1", "b"])
            action, state = _prompt_save_slot_selection(
                renderer, ["01_test"], input_fn=lambda _: next(inputs)
            )
            assert action == "new"
            # Should have rendered error about corrupted save
            assert any("save" in line.lower() for line in renderer.lines)
        finally:
            main_mod.SAVES_DIR = old_saves

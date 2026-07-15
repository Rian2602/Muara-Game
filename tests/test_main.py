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

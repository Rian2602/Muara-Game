"""Shared test fixtures for Muara CLI narrative engine."""

from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from muara.engine.chapter_loader import load_chapter
from muara.engine.render_cli import CLIRenderer
from muara.engine.state import GameState
from muara.models.chapter import Chapter, Scene
from muara.models.save_state import SaveState

CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "content" / "chapters"


@pytest.fixture
def make_console():
    """Return a Console that writes to StringIO (suppresses terminal output)."""
    def _factory() -> Console:
        return Console(file=StringIO(), force_terminal=True)
    return _factory


@pytest.fixture
def make_renderer():
    """Return a CLIRenderer that writes to StringIO (suppresses terminal output)."""
    def _factory() -> CLIRenderer:
        console = Console(file=StringIO(), force_terminal=True)
        return CLIRenderer(console)
    return _factory


@pytest.fixture
def minimal_scene() -> Scene:
    """Minimal valid Scene — useful for Chapter construction in tests."""
    return Scene(id="scene_1", text="Teks test.", next_chapter="__END__")


@pytest.fixture
def minimal_chapter(minimal_scene: Scene) -> Chapter:
    """Minimal valid Chapter — use as a building block in tests."""
    return Chapter(
        id="test_ch",
        title="TEST CHAPTER",
        location="Lokasi Test",
        date="1 Januari 1900",
        time="00.00",
        scenes=[minimal_scene],
    )


@pytest.fixture
def minimal_save() -> SaveState:
    """Minimal valid SaveState."""
    return SaveState(
        save_id="test_save",
        current_chapter="test_ch",
        current_scene="scene_1",
    )


@pytest.fixture
def ch1() -> Chapter:
    """Load the real 01_pembukaan chapter."""
    return load_chapter(CHAPTERS_DIR / "01_pembukaan.yaml")


@pytest.fixture
def fresh_state() -> GameState:
    """A brand new playthrough GameState."""
    return GameState.new_playthrough("test", "01", "scene_1")

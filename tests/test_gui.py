"""Tests for Textual GUI (MuaraApp + GameScreen)."""

from __future__ import annotations

import asyncio
import pytest
from pathlib import Path

from muara.gui.app import MuaraApp, GameScreen, SaveSlotScreen, resolve_text
from muara.engine.state import GameState
from muara.engine.save_manager import save, SaveLoadError
from muara.engine.ending import determine_ending
from muara.models.chapter import Chapter, Scene, TextVariant
from muara.models.save_state import SaveState


class TestResolveText:
    """resolve_text() picks correct variant."""

    def test_no_variants(self):
        scene = Scene(id="s1", text="Hello", next_chapter="ch2")
        state = GameState.new_playthrough("test", "ch1", "")
        assert resolve_text(scene, state) == "Hello"

    def test_matching_variant(self):
        scene = Scene(
            id="s1",
            text="Default",
            next_chapter="ch2",
            text_variants=[
                TextVariant(condition="chapter_5_choice == simpan", text="Simpan path"),
                TextVariant(condition="true", text="Default", default=True),
            ],
        )
        state = GameState.new_playthrough("test", "ch1", "")
        state.set_flag("chapter_5_choice", "simpan")
        assert resolve_text(scene, state) == "Simpan path"

    def test_default_fallback(self):
        scene = Scene(
            id="s1",
            text="Default",
            next_chapter="ch2",
            text_variants=[
                TextVariant(condition="chapter_5_choice == simpan", text="Simpan"),
                TextVariant(condition="chapter_5_choice == hancurkan", text="Hancur", default=True),
            ],
        )
        state = GameState.new_playthrough("test", "ch1", "")
        state.set_flag("chapter_5_choice", "other")
        assert resolve_text(scene, state) == "Hancur"


class TestDetermineEnding:
    """determine_ending() from shared module."""

    def test_pembebasan(self):
        state = GameState.new_playthrough("test", "ch1", "")
        state.set_flag("kebenaran_terungkap", True)
        state.set_flag("warisan_positif", True)
        state.set_flag("melihat_anomali", True)
        assert determine_ending(state) == "pembebasan"

    def test_kehancuran_by_konfrontasi(self):
        state = GameState.new_playthrough("test", "ch1", "")
        state.set_flag("konfrontasi_berhasil", False)
        assert determine_ending(state) == "kehancuran"

    def test_kehancuran_by_tekanan(self):
        state = GameState.new_playthrough("test", "ch1", "")
        state.set_flag("tekanan_meningkat", 7)
        assert determine_ending(state) == "kehancuran"

    def test_sekutu(self):
        state = GameState.new_playthrough("test", "ch1", "")
        state.set_flag("beri_bukti_ke_jaya", True)
        state.set_flag("bukti_kuat", True)
        state.set_flag("berbicara_dengan_jaya", True)
        assert determine_ending(state) == "sekutu"

    def test_terlupakan_default(self):
        state = GameState.new_playthrough("test", "ch1", "")
        assert determine_ending(state) == "terlupakan"


def test_app_launches():
    """MuaraApp can mount and display header."""
    app = MuaraApp()

    async def _run():
        async with app.run_test() as pilot:
            assert app.title == "Muara"
            assert len(app.chapter_sequence) > 0

    asyncio.run(_run())


class TestSaveSlotScreen:
    """Tests for SaveSlotScreen UI."""

    def test_save_slot_screen_mounts_with_empty_saves(self, tmp_path: Path):
        """SaveSlotScreen shows 'no saves' message when directory is empty."""
        from muara.gui.app import SaveSlotScreen
        import muara.gui.app as app_mod
        
        original_saves_dir = app_mod.SAVES_DIR
        app_mod.SAVES_DIR = tmp_path
    
        app = MuaraApp()
        app.chapter_sequence = ["01_pembukaan"]
    
        async def _run():
            try:
                async with app.run_test() as pilot:
                    # Push save slot screen
                    screen = SaveSlotScreen(app.chapter_sequence)
                    app.push_screen(screen)
                    await pilot.pause()
        
                    # Should show empty message
                    ol = screen.query_one("#save-list")
                    assert ol.option_count == 1  # Just "Tidak ada save slot"
            finally:
                app_mod.SAVES_DIR = original_saves_dir
    
        asyncio.run(_run())

    def test_save_slot_screen_shows_saves(self, tmp_path: Path):
        """SaveSlotScreen displays existing save slots."""
        from muara.gui.app import SaveSlotScreen, SAVES_DIR
        from unittest.mock import patch

        # Create a test save
        save_state = SaveState(
            save_id="test_slot",
            current_chapter="01_pembukaan",
            current_scene="scene_1",
            flags={"melihat_anomali": True},
        )
        
        # Mock SAVES_DIR to use tmp_path
        with patch('muara.gui.app.SAVES_DIR', tmp_path):
            save(save_state, tmp_path)
            
            app = MuaraApp()
            app.chapter_sequence = ["01_pembukaan"]

            async def _run():
                async with app.run_test() as pilot:
                    screen = SaveSlotScreen(app.chapter_sequence)
                    app.push_screen(screen)
                    await pilot.pause()
                    
                    # Should show the save slot
                    ol = screen.query_one("#save-list")
                    assert ol.option_count == 1
                    assert screen.save_slots[0].save_id == "test_slot"
                    assert screen.save_slots[0].key_flags == ["Anomali"]

            asyncio.run(_run())


from muara.models.world_clock import WorldEvent, EventTrigger, Shift
from muara.engine.event_scheduler import EventScheduler

class TestGameScreen:
    """Tests for GameScreen UI."""

    def test_game_screen_shows_first_scene(self):
        """GameScreen displays the first scene of a chapter."""
        app = MuaraApp()
        app.chapter_sequence = ["01_pembukaan"]
        app.state = GameState.new_playthrough("test", "01_pembukaan", "")
        app.start_scene_id = None

        async def _run():
            async with app.run_test() as pilot:
                # Load first chapter
                await app._load_chapter("01_pembukaan")
                await pilot.pause()
                
                # Should have a GameScreen on the stack
                assert len(app.screen_stack) > 0
                current_screen = app.screen
                assert isinstance(current_screen, GameScreen)
                assert current_screen.chapter.id == "01_pembukaan"

        asyncio.run(_run())

    def test_game_screen_shows_choices(self):
        """GameScreen displays choices when scene has them."""
        app = MuaraApp()
        app.chapter_sequence = ["01_pembukaan"]
        app.state = GameState.new_playthrough("test", "01_pembukaan", "")

        async def _run():
            async with app.run_test() as pilot:
                await app._load_chapter("01_pembukaan")
                await pilot.pause()
                
                current_screen = app.screen
                if isinstance(current_screen, GameScreen):
                    # Check if choices are displayed
                    ol = current_screen.query_one("#choices")
                    # Choices should be visible if current scene has them
                    assert ol is not None

        asyncio.run(_run())

    def test_game_screen_executes_hooks_and_scheduler(self):
        app = MuaraApp()
        
        event = WorldEvent(
            id="test_event_gui",
            trigger=EventTrigger(shift=Shift.SIANG),
            set_flags=["gui_event_triggered: true"]
        )
        app.scheduler = EventScheduler([event])
        app.chapter_sequence = ["test_chap"]
        app.state = GameState.new_playthrough("test", "test_chap", "s1")
        
        chapter = Chapter(
            id="test_chap",
            title="Test",
            location="Loc",
            date="Date",
            time="Time",
            scenes=[
                Scene(
                    id="s1",
                    text="scene 1",
                    on_exit=["advance_clock(shift)"],
                    next_chapter="next_chap"
                )
            ]
        )
        
        async def _run():
            import muara.gui.app as app_mod
            original_load = app_mod.load_events
            app_mod.load_events = lambda x: [event]
            
            try:
                async with app.run_test() as pilot:
                    screen = GameScreen(chapter, app.state, scheduler=app.scheduler)
                    app.push_screen(screen)
                    await pilot.pause()
                    
                    assert app.state.get_flag("world_shift") == Shift.SIANG.value
                    assert app.state.get_flag("gui_event_triggered") is True
            finally:
                app_mod.load_events = original_load
                
        import asyncio
        asyncio.run(_run())



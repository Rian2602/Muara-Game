"""Tests for Textual GUI (MuaraApp + GameScreen)."""

from __future__ import annotations

import asyncio
import pytest
from pathlib import Path

from muara.gui.app import MuaraApp, GameScreen, resolve_text
from muara.engine.state import GameState
from muara.engine.ending import determine_ending
from muara.models.chapter import Chapter, Scene, TextVariant


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

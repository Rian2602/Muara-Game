from datetime import datetime

import pytest

from muara.engine.state import GameState
from muara.models.save_state import SaveState


def _new_state() -> GameState:
    return GameState.new_playthrough(
        save_id="test", chapter_id="01_test", scene_id="scene_1"
    )


def test_increment_counter_from_zero():
    state = _new_state()
    result = state.increment_counter("kunjungan")
    assert result == 1
    assert state.get_flag("kunjungan") == 1


def test_increment_counter_from_existing_value():
    state = _new_state()
    state.set_flag("kunjungan", 5)
    result = state.increment_counter("kunjungan", by=3)
    assert result == 8


def test_increment_counter_rejects_boolean_flag():
    state = _new_state()
    state.set_flag("sudah_lapor", True)
    with pytest.raises(TypeError):
        state.increment_counter("sudah_lapor")


def test_add_to_set_is_idempotent():
    state = _new_state()
    state.add_to_set("evidence_found", "kotak_kayu")
    state.add_to_set("evidence_found", "kotak_kayu")
    assert state.save_state.flag_sets["evidence_found"] == ["kotak_kayu"]


def test_set_contains_on_nonexistent_set_returns_false():
    state = _new_state()
    assert state.set_contains("belum_pernah_dibuat", "apa_saja") is False


def test_set_contains_finds_added_item():
    state = _new_state()
    state.add_to_set("evidence_found", "jangka_sorong")
    assert state.set_contains("evidence_found", "jangka_sorong") is True

from muara.models.world_clock import Shift

def test_advance_clock_shift(fresh_state):
    fresh_state.advance_clock_shift()
    assert fresh_state.get_flag("world_day") == 1
    assert fresh_state.get_flag("world_shift") == Shift.SIANG.value
    
    fresh_state.advance_clock_shift()
    assert fresh_state.get_flag("world_shift") == Shift.MALAM.value
    
    fresh_state.advance_clock_shift()
    assert fresh_state.get_flag("world_day") == 2
    assert fresh_state.get_flag("world_shift") == Shift.PAGI.value

def test_advance_clock_day(fresh_state):
    fresh_state.advance_clock_shift() # shift is now SIANG
    fresh_state.advance_clock_day()
    assert fresh_state.get_flag("world_day") == 2
    assert fresh_state.get_flag("world_shift") == Shift.PAGI.value

def test_clock_flags_evaluation(fresh_state):
    fresh_state.advance_clock_shift()
    assert fresh_state.evaluate_condition("world_day == 1") is True
    assert fresh_state.evaluate_condition("world_shift == siang") is True
    
    fresh_state.advance_clock_day()
    assert fresh_state.evaluate_condition("world_day >= 2") is True
    assert fresh_state.evaluate_condition("world_shift == pagi") is True

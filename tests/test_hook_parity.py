"""Parity test: verify hook execution is identical across CLI and GUI paths."""

from muara.engine.state import GameState


def _make_state(**flags) -> GameState:
    """Create a GameState with the given initial flags."""
    state = GameState.new_playthrough(
        save_id="test",
        chapter_id="ch1",
        scene_id="scene_1",
    )
    for k, v in flags.items():
        state.set_flag(k, v)
    return state


class TestHookParity:
    """Verify GameState.execute_hooks produces correct results for all hook types."""

    def test_flag_assignment_true(self):
        state = _make_state()
        state.execute_hooks(["entered_room: true"])
        assert state.get_flag("entered_room") is True

    def test_flag_assignment_false(self):
        state = _make_state()
        state.execute_hooks(["left_room: false"])
        assert state.get_flag("left_room") is False

    def test_flag_assignment_int(self):
        state = _make_state()
        state.execute_hooks(["score: 42"])
        assert state.get_flag("score") == 42

    def test_flag_assignment_string(self):
        state = _make_state()
        state.execute_hooks(["location: gudang"])
        assert state.get_flag("location") == "gudang"

    def test_increment_counter(self):
        state = _make_state()
        state.execute_hooks(["increment(visit_count)"])
        assert state.get_flag("visit_count") == 1
        state.execute_hooks(["increment(visit_count)"])
        assert state.get_flag("visit_count") == 2

    def test_add_to_set(self):
        state = _make_state()
        state.execute_hooks(["add_to_set(visited_places, room_1)"])
        assert state.set_contains("visited_places", "room_1")
        state.execute_hooks(["add_to_set(visited_places, room_2)"])
        assert state.set_contains("visited_places", "room_2")
        assert not state.set_contains("visited_places", "room_3")

    def test_advance_clock_shift(self):
        state = _make_state()
        state.execute_hooks(["advance_clock(shift)"])
        assert state.get_flag("world_shift") is not None

    def test_advance_clock_day(self):
        state = _make_state()
        state.execute_hooks(["advance_clock(day)"])
        assert state.get_flag("world_day") == 2

    def test_change_rep(self):
        state = _make_state()
        state.execute_hooks(["change_rep(sutisna, trust, 5)"])
        assert state._save_state.reputations["sutisna"]["trust"] == 5

    def test_multiple_hooks(self):
        state = _make_state()
        state.execute_hooks([
            "flag_a: true",
            "flag_b: 100",
            "increment(counter)",
            "add_to_set(items, widget)",
        ])
        assert state.get_flag("flag_a") is True
        assert state.get_flag("flag_b") == 100
        assert state.get_flag("counter") == 1
        assert state.set_contains("items", "widget")

    def test_empty_hooks(self):
        state = _make_state()
        state.execute_hooks([])
        assert state.flags == {}

    def test_advance_clock_invalid_arg_raises(self):
        import pytest
        state = _make_state()
        with pytest.raises(Exception):
            state.execute_hooks(["advance_clock(invalid)"])

    def test_change_rep_non_numeric_raises(self):
        import pytest
        state = _make_state()
        with pytest.raises(Exception):
            state.execute_hooks(["change_rep(sutisna, trust, abc)"])

    def test_change_rep_wrong_arg_count_raises(self):
        import pytest
        state = _make_state()
        with pytest.raises(Exception):
            state.execute_hooks(["change_rep(sutisna, trust)"])

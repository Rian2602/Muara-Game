import pytest
from pydantic import ValidationError

from muara.models.world_clock import Shift, WorldClock, EventTrigger, WorldEvent
from muara.models.chapter import FlagCondition, ConditionOperator


def test_shift_next():
    assert Shift.PAGI.next() == (Shift.SIANG, False)
    assert Shift.SIANG.next() == (Shift.MALAM, False)
    assert Shift.MALAM.next() == (Shift.PAGI, True)


def test_world_clock_default():
    clock = WorldClock()
    assert clock.day == 1
    assert clock.shift == Shift.PAGI


def test_world_clock_advance_shift():
    clock = WorldClock()
    
    clock = clock.advance_shift()
    assert clock.day == 1
    assert clock.shift == Shift.SIANG
    
    clock = clock.advance_shift()
    assert clock.day == 1
    assert clock.shift == Shift.MALAM
    
    clock = clock.advance_shift()
    assert clock.day == 2
    assert clock.shift == Shift.PAGI


def test_world_clock_advance_day():
    clock = WorldClock(day=1, shift=Shift.SIANG)
    clock = clock.advance_day()
    assert clock.day == 2
    assert clock.shift == Shift.PAGI


def test_event_trigger_validation():
    # Only day
    trigger1 = EventTrigger(day=2)
    assert trigger1.day == 2
    assert trigger1.shift is None
    
    # Only shift
    trigger2 = EventTrigger(shift=Shift.MALAM)
    assert trigger2.shift == Shift.MALAM
    assert trigger2.day is None
    
    # Only flags
    cond = FlagCondition(flag="test_flag", operator=ConditionOperator.EQ, value=True)
    trigger3 = EventTrigger(flags=[cond])
    assert len(trigger3.flags) == 1
    
    # Combination
    trigger4 = EventTrigger(day=3, shift=Shift.PAGI, flags=[cond])
    assert trigger4.day == 3
    assert trigger4.shift == Shift.PAGI
    assert len(trigger4.flags) == 1


def test_world_event_validation():
    trigger = EventTrigger(day=2)
    event = WorldEvent(
        id="test_event",
        trigger=trigger,
        set_flags=["flag1: true"],
        repeatable=True
    )
    assert event.id == "test_event"
    assert event.set_flags == ["flag1: true"]
    assert event.repeatable is True

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        WorldEvent(
            id="test_event",
            trigger=trigger,
            extra_field="invalid"
        )

from muara.models.save_state import SaveState

def test_savestate_v1_migration():
    # JSON literal string representing a full SaveState v1, without world_clock
    v1_json = """
    {
        "version": 1,
        "save_id": "test_save",
        "player_name": null,
        "current_chapter": "01_pembukaan",
        "current_scene": "scene_1",
        "completed": false,
        "flags": {"some_flag": true},
        "flag_sets": {"some_set": ["item1"]},
        "chapters_completed": ["01_pembukaan"],
        "endings_achieved": [],
        "last_saved": "2026-07-14T10:00:00Z",
        "playthrough_start": "2026-07-14T09:00:00Z"
    }
    """
    state = SaveState.model_validate_json(v1_json)
    assert state.version == 1
    assert state.save_id == "test_save"
    # world_clock should be populated with defaults
    assert state.world_clock.day == 1
    assert state.world_clock.shift == Shift.PAGI

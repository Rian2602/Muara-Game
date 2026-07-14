from muara.engine.state import GameState
from muara.engine.event_scheduler import EventScheduler, FIRED_EVENTS_SET
from muara.models.world_clock import WorldEvent, EventTrigger, Shift
from muara.models.chapter import FlagCondition, ConditionOperator


def test_event_scheduler_day_match(fresh_state):
    event = WorldEvent(
        id="day_event",
        trigger=EventTrigger(day=2),
        set_flags=["day_matched: true"]
    )
    scheduler = EventScheduler([event])
    
    # world_clock day is 1 by default, but it's not projected until advance
    # but initially world_day flag is None, let's sync it first
    fresh_state.advance_clock_shift() # now siang, day 1
    
    # Not due yet
    assert len(scheduler.due_events(fresh_state)) == 0
    
    # Advance to day 2
    fresh_state.advance_clock_day() # day 2, pagi
    due = scheduler.due_events(fresh_state)
    assert len(due) == 1
    assert due[0].id == "day_event"


def test_event_scheduler_shift_match(fresh_state):
    event = WorldEvent(
        id="shift_event",
        trigger=EventTrigger(shift=Shift.MALAM),
        set_flags=["shift_matched: true"]
    )
    scheduler = EventScheduler([event])
    
    fresh_state.advance_clock_shift() # day 1, siang
    assert len(scheduler.due_events(fresh_state)) == 0
    
    fresh_state.advance_clock_shift() # day 1, malam
    due = scheduler.due_events(fresh_state)
    assert len(due) == 1
    assert due[0].id == "shift_event"


def test_event_scheduler_flags_match(fresh_state):
    cond1 = FlagCondition(flag="flag1", operator=ConditionOperator.EQ, value=True)
    cond2 = FlagCondition(flag="flag2", operator=ConditionOperator.GTE, value=5)
    
    event = WorldEvent(
        id="flags_event",
        trigger=EventTrigger(flags=[cond1, cond2]),
        set_flags=["flags_matched: true"]
    )
    scheduler = EventScheduler([event])
    
    # Empty flags -> not due
    assert len(scheduler.due_events(fresh_state)) == 0
    
    # Partial match -> not due
    fresh_state.set_flag("flag1", True)
    fresh_state.set_flag("flag2", 3)
    assert len(scheduler.due_events(fresh_state)) == 0
    
    # Full match -> due
    fresh_state.set_flag("flag2", 5)
    due = scheduler.due_events(fresh_state)
    assert len(due) == 1


def test_event_non_repeatable(fresh_state):
    event = WorldEvent(
        id="one_shot",
        trigger=EventTrigger(day=2),
        set_flags=["applied: true"],
        repeatable=False
    )
    scheduler = EventScheduler([event])
    
    fresh_state.advance_clock_day() # day 2, pagi
    
    # Due initially
    due = scheduler.due_events(fresh_state)
    assert len(due) == 1
    
    # Apply
    scheduler.apply_event(due[0], fresh_state)
    assert fresh_state.get_flag("applied") is True
    assert fresh_state.set_contains(FIRED_EVENTS_SET, "one_shot") is True
    
    # Not due anymore
    due_after = scheduler.due_events(fresh_state)
    assert len(due_after) == 0


def test_event_repeatable(fresh_state):
    event = WorldEvent(
        id="repeatable",
        trigger=EventTrigger(shift=Shift.PAGI),
        set_flags=["counter_str: up"],
        repeatable=True
    )
    scheduler = EventScheduler([event])
    
    fresh_state.advance_clock_day() # day 2, pagi
    
    # Due
    due = scheduler.due_events(fresh_state)
    assert len(due) == 1
    
    # Apply
    scheduler.apply_event(due[0], fresh_state)
    
    # Still due because repeatable
    due_after = scheduler.due_events(fresh_state)
    assert len(due_after) == 1

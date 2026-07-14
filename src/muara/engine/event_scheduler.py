from __future__ import annotations

from muara.engine.state import GameState
from muara.models.chapter import FlagAssignment
from muara.models.world_clock import WorldEvent

FIRED_EVENTS_SET = "_fired_world_events"


class EventScheduler:
    def __init__(self, events: list[WorldEvent]) -> None:
        self._events = events

    def due_events(self, state: GameState) -> list[WorldEvent]:
        """Kembalikan semua event yang due dan BELUM diterapkan (untuk non-repeatable).
        
        TIDAK menerapkan efeknya — hanya menentukan mana yang due. Pemanggilan
        apply_event() adalah langkah terpisah, disengaja, agar due_events() tetap
        pure function yang mudah diuji tanpa mutasi state.
        """
        due = []
        for event in self._events:
            if not self._matches_trigger(event, state):
                continue
            if not event.repeatable and state.set_contains(FIRED_EVENTS_SET, event.id):
                continue
            due.append(event)
        return due

    def apply_event(self, event: WorldEvent, state: GameState) -> None:
        """Terapkan efek flag sebuah event dan catat sebagai 'sudah fired'."""
        for raw in event.set_flags:
            assignment = FlagAssignment.from_raw_string(raw)
            state.set_flag(assignment.key, assignment.value)
        if not event.repeatable:
            state.add_to_set(FIRED_EVENTS_SET, event.id)

    def _matches_trigger(self, event: WorldEvent, state: GameState) -> bool:
        trigger = event.trigger
        if trigger.day is not None and state.get_flag("world_day") != trigger.day:
            return False
        if trigger.shift is not None and state.get_flag("world_shift") != trigger.shift.value:
            return False
        if trigger.flags:
            flags = state.save_state.flags
            if not all(cond.evaluate(flags) for cond in trigger.flags):
                return False
        return True

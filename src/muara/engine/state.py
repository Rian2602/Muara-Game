from __future__ import annotations

import re
from datetime import datetime, timezone

from muara.models.save_state import SaveState
from muara.models.npc import NPCEntity

class GameState:
    """Wrapper mutable di atas SaveState untuk dipakai selama satu sesi main."""
    
    def __init__(self, save_state: SaveState) -> None:
        self._save_state = save_state
        self._completed_set: set[str] = set(save_state.chapters_completed)
        self.npcs: list[NPCEntity] = []

    @property
    def save_state(self) -> SaveState:
        return self._save_state

    @property
    def current_chapter(self) -> str:
        return self._save_state.current_chapter

    @property
    def current_scene(self) -> str:
        return self._save_state.current_scene

    @property
    def flags(self) -> dict[str, bool | str | int]:
        return self._save_state.flags

    def set_flag(self, key: str, value: bool | str | int) -> None:
        self._save_state.flags[key] = value

    def get_flag(
        self, key: str, default: bool | str | int | None = None
    ) -> bool | str | int | None:
        return self._save_state.flags.get(key, default)

    def increment_counter(self, key: str, by: int = 1) -> int:
        """Increment sebuah flag integer. Jika belum ada, mulai dari 0.
        Raises TypeError jika flag itu sudah ada tapi bukan int."""
        current = self._save_state.flags.get(key, 0)
        if not isinstance(current, int) or isinstance(current, bool):
            raise TypeError(
                f"Flag {key!r} bukan integer (nilai saat ini: {current!r}), "
                "tidak bisa di-increment sebagai counter."
            )
        new_value = current + by
        self._save_state.flags[key] = new_value
        return new_value

    def add_to_set(self, set_name: str, item: str) -> None:
        """Tambah satu item ke flag_sets[set_name]. Idempotent."""
        current_set = self._save_state.flag_sets.setdefault(set_name, [])
        if item not in current_set:
            current_set.append(item)

    def set_contains(self, set_name: str, item: str) -> bool:
        """Cek keanggotaan di flag_sets[set_name]."""
        return item in self._save_state.flag_sets.get(set_name, [])

    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate a simple condition string against current flags.

        Supported formats:
        - "flag_name"            → truthy check (flag exists and is truthy)
        - "flag_name == true"    → boolean equality
        - "flag_name == false"   → boolean equality
        - "flag_name != true"    → boolean inequality
        - "flag_name == value"   → string/int equality
        - "flag_name >= value"   → numeric comparison
        - "flag_name <= value"   → numeric comparison
        - "not flag_name"        → negation
        """
        condition = condition.strip()

        if condition.startswith("not "):
            inner = condition[4:].strip()
            return not self.evaluate_condition(inner)

        for op in (">=", "<=", "!=", "=="):
            if op in condition:
                key, _, val = condition.partition(op)
                key = key.strip()
                val = val.strip()
                flag_val = self._save_state.flags.get(key)
                if flag_val is None:
                    return False
                return self._compare(flag_val, op, val)

        flag_val = self._save_state.flags.get(condition)
        return bool(flag_val)

    def _compare(self, flag_val: bool | str | int, op: str, val: str) -> bool:
        if isinstance(flag_val, bool):
            if val.lower() == "true":
                return flag_val is True if op == "==" else flag_val is not True
            if val.lower() == "false":
                return flag_val is False if op == "==" else flag_val is not False
        if isinstance(flag_val, int) and op in (">=", "<="):
            try:
                num = int(val)
                return flag_val >= num if op == ">=" else flag_val <= num
            except ValueError:
                return False
        if op == "==":
            if val.lower() == "true":
                return flag_val is True
            if val.lower() == "false":
                return flag_val is False
            try:
                return flag_val == int(val)
            except ValueError:
                return flag_val == val
        if op == "!=":
            if val.lower() == "true":
                return flag_val is not True
            if val.lower() == "false":
                return flag_val is not False
            try:
                return flag_val != int(val)
            except ValueError:
                return flag_val != val
        return False

    def advance_to(self, chapter_id: str, scene_id: str) -> None:
        self._save_state.current_chapter = chapter_id
        self._save_state.current_scene = scene_id

    def mark_chapter_complete(self, chapter_id: str) -> None:
        if chapter_id not in self._completed_set:
            self._save_state.chapters_completed.append(chapter_id)
            self._completed_set.add(chapter_id)

    def touch_last_saved(self) -> None:
        self._save_state.last_saved = datetime.now(timezone.utc)

    def advance_clock_shift(self) -> None:
        """Majukan world_clock satu shift, sinkronkan flag proyeksi."""
        new_clock = self._save_state.world_clock.advance_shift()
        self._save_state.world_clock = new_clock
        self._sync_clock_flags()

    def advance_clock_day(self) -> None:
        """Majukan world_clock satu hari penuh, sinkronkan flag proyeksi."""
        new_clock = self._save_state.world_clock.advance_day()
        self._save_state.world_clock = new_clock
        self._sync_clock_flags()

    def change_reputation(self, npc_id: str, rep_type: str, amount: int) -> None:
        """Ubah nilai reputasi (trust, fear, dll) untuk seorang NPC."""
        npc_reps = self._save_state.reputations.setdefault(npc_id, {})
        current = npc_reps.get(rep_type, 0)
        npc_reps[rep_type] = current + amount

    def _sync_clock_flags(self) -> None:
        """Proyeksikan world_clock ke flags biasa agar bisa dibaca evaluate_condition().
        
        Dipanggil setiap kali clock berubah. Flag ini adalah TURUNAN, jangan pernah
        di-set manual lewat set_flag() — akan langsung tertimpa saat clock maju lagi.
        """
        self.set_flag("world_day", self._save_state.world_clock.day)
        self.set_flag("world_shift", self._save_state.world_clock.shift.value)
        self._sync_npc_locations()

    def _sync_npc_locations(self) -> None:
        current_shift = self._save_state.world_clock.shift
        for npc in self.npcs:
            loc = npc.default_location
            for sch in npc.schedules:
                if sch.shift == current_shift:
                    loc = sch.location
                    break
            self.set_flag(f"npc_{npc.id}_location", loc)

    @classmethod
    def new_playthrough(
        cls,
        save_id: str,
        chapter_id: str,
        scene_id: str,
        player_name: str | None = None,
    ) -> "GameState":
        now = datetime.now(timezone.utc)
        return cls(
            SaveState(
                save_id=save_id,
                player_name=player_name,
                current_chapter=chapter_id,
                current_scene=scene_id,
                last_saved=now,
                playthrough_start=now,
            )
        )

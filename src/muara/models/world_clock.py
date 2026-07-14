from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict
from muara.models.chapter import FlagCondition


class Shift(str, Enum):
    PAGI = "pagi"
    SIANG = "siang"
    MALAM = "malam"

    def next(self) -> tuple["Shift", bool]:
        """Kembalikan shift berikutnya dan apakah hari berganti.
        
        Returns:
            (shift_berikutnya, hari_berganti: bool)
        """
        order = [Shift.PAGI, Shift.SIANG, Shift.MALAM]
        current_index = order.index(self)
        if current_index == len(order) - 1:
            return Shift.PAGI, True
        return order[current_index + 1], False


class WorldClock(BaseModel):
    """Representasi waktu dunia yang bisa dievaluasi mesin.
    
    TIDAK menggantikan Chapter.date/Chapter.time (yang tetap string display untuk
    prosa). Ini adalah lapisan terpisah yang disinkronkan ke flags proyeksi
    (world_day, world_shift) agar bisa dibaca lewat evaluate_condition() yang
    sudah ada tanpa mengubah parsernya.
    """
    model_config = ConfigDict(extra="forbid")

    day: int = 1
    shift: Shift = Shift.PAGI

    def advance_shift(self) -> "WorldClock":
        """Kembalikan WorldClock baru setelah maju satu shift."""
        next_shift, day_changed = self.shift.next()
        return WorldClock(
            day=self.day + 1 if day_changed else self.day,
            shift=next_shift,
        )

    def advance_day(self) -> "WorldClock":
        """Kembalikan WorldClock baru setelah maju satu hari penuh (shift kembali ke pagi)."""
        return WorldClock(day=self.day + 1, shift=Shift.PAGI)


class EventTrigger(BaseModel):
    """Syarat sebuah WorldEvent dianggap 'due'.
    
    Semua field yang diisi (bukan None) harus cocok — AND, bukan OR. Untuk logika
    OR, definisikan event terpisah.
    """
    model_config = ConfigDict(extra="forbid")

    day: int | None = None
    shift: Shift | None = None
    flags: list[FlagCondition] | None = None


class WorldEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    trigger: EventTrigger
    set_flags: list[str] = []
    repeatable: bool = False

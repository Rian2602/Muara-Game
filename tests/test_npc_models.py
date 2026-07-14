import pytest
from pydantic import ValidationError
from muara.models.npc import NPCEntity, NPCSchedule
from muara.models.world_clock import Shift


def test_npc_entity_valid():
    npc = NPCEntity(
        id="sutisna",
        name="Sutisna",
        traits=["tegas", "diam"],
        default_location="gudang_utama",
        schedules=[
            NPCSchedule(shift=Shift.SIANG, location="kantor_mandor")
        ]
    )
    assert npc.id == "sutisna"
    assert npc.name == "Sutisna"
    assert npc.traits == ["tegas", "diam"]
    assert npc.default_location == "gudang_utama"
    assert len(npc.schedules) == 1
    assert npc.schedules[0].shift == Shift.SIANG
    assert npc.schedules[0].location == "kantor_mandor"


def test_npc_entity_extra_forbid():
    with pytest.raises(ValidationError):
        NPCEntity(
            id="kusuma",
            name="Kusuma",
            default_location="pelabuhan",
            invalid_field="test"
        )


def test_npc_schedule_extra_forbid():
    with pytest.raises(ValidationError):
        NPCSchedule(
            shift=Shift.PAGI,
            location="pelabuhan",
            invalid_field="test"
        )

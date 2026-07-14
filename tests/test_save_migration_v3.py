from muara.models.save_state import SaveState
from muara.models.world_clock import Shift

def test_savestate_v2_migration():
    # JSON literal string representing a full SaveState v2
    v2_json = """
    {
        "version": 2,
        "save_id": "test_save_v2",
        "player_name": null,
        "current_chapter": "01_pembukaan",
        "current_scene": "scene_1",
        "completed": false,
        "flags": {"some_flag": true},
        "flag_sets": {"some_set": ["item1"]},
        "chapters_completed": ["01_pembukaan"],
        "endings_achieved": [],
        "last_saved": "2026-07-14T10:00:00Z",
        "playthrough_start": "2026-07-14T09:00:00Z",
        "world_clock": {"day": 2, "shift": "siang"}
    }
    """
    state = SaveState.model_validate_json(v2_json)
    assert state.version == 2
    assert state.save_id == "test_save_v2"
    assert state.world_clock.day == 2
    assert state.world_clock.shift == Shift.SIANG
    # reputations should be populated with defaults
    assert state.reputations == {}

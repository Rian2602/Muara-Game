"""Verifikasi engine: ChapterRunner (input injection), GameState, save_manager."""

from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from pydantic import ValidationError

from muara.constants import END_OF_STORY_MARKER
from muara.engine.chapter_loader import load_chapter
from muara.engine.chapter_runner import ChapterRunner, ChapterRunError
from muara.engine.render_cli import CLIRenderer
from muara.engine.save_manager import SaveLoadError, save, load, list_saves
from muara.engine.state import GameState
from muara.models.save_state import SaveState

CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "content" / "chapters"


def make_runner(
    chapter_id: str,
    scene_id: str = "scene_1",
    flags: dict | None = None,
    input_values: list[str] | None = None,
):
    path = CHAPTERS_DIR / f"{chapter_id}.yaml"
    chapter = load_chapter(path)
    sv = SaveState(
        save_id="test_run",
        current_chapter=chapter_id,
        current_scene=scene_id,
        flags=flags or {},
    )
    state = GameState(sv)
    console = Console(file=StringIO(), force_terminal=True)
    renderer = CLIRenderer(console)

    input_iter = iter(input_values) if input_values else iter([])

    def scripted_input(prompt: str = "") -> str:
        try:
            return next(input_iter)
        except StopIteration:
            raise RuntimeError("Scripted input exhausted — more input values needed")

    return ChapterRunner(chapter, state, renderer, input_fn=scripted_input), state, console


def run_chapter(chapter_id: str, state: GameState, input_sequence: list[str]) -> str | None:
    """Run a single chapter with scripted input, return next_chapter."""
    path = CHAPTERS_DIR / f"{chapter_id}.yaml"
    chapter = load_chapter(path)
    console = Console(file=StringIO(), force_terminal=True)
    renderer = CLIRenderer(console)
    input_iter = iter(input_sequence)

    def scripted_input(prompt: str = "") -> str:
        try:
            return next(input_iter)
        except StopIteration:
            raise RuntimeError("Scripted input exhausted — more input values needed")

    runner = ChapterRunner(chapter, state, renderer, input_fn=scripted_input)
    return runner.run()


class TestChapterRunner:
    def test_ch1_option_a(self):
        state = GameState.new_playthrough("t", "01_pembukaan", "")
        next_ch = run_chapter("01_pembukaan", state, ["", "", "", "1"])
        assert state.get_flag("melihat_anomali") is True
        assert next_ch == "02_gejala"

    def test_ch1_option_b(self):
        state = GameState.new_playthrough("t", "01_pembukaan", "")
        next_ch = run_chapter("01_pembukaan", state, ["", "", "", "2"])
        assert state.get_flag("melihat_anomali") is False
        assert next_ch == "02_gejala"

    def test_invalid_input_retries(self):
        state = GameState.new_playthrough("t", "01_pembukaan", "")
        next_ch = run_chapter("01_pembukaan", state, ["", "", "", "abc", "0", "5", "1"])
        assert state.get_flag("melihat_anomali") is True
        assert next_ch == "02_gejala"

    def test_start_scene_resume(self):
        path = CHAPTERS_DIR / "01_pembukaan.yaml"
        chapter = load_chapter(path)
        sv = SaveState(
            save_id="t",
            current_chapter="01_pembukaan",
            current_scene="scene_4",
        )
        state = GameState(sv)
        console = Console(file=StringIO(), force_terminal=True)
        renderer = CLIRenderer(console)
        input_iter = iter(["1"])

        def scripted_input(prompt: str = "") -> str:
            return next(input_iter)

        runner = ChapterRunner(chapter, state, renderer, input_fn=scripted_input)
        next_ch = runner.run(start_scene_id="scene_4")
        assert state.get_flag("melihat_anomali") is True
        assert next_ch == "02_gejala"

    def test_invalid_start_scene_raises(self):
        path = CHAPTERS_DIR / "01_pembukaan.yaml"
        chapter = load_chapter(path)
        sv = SaveState(save_id="t", current_chapter="01_pembukaan", current_scene="")
        state = GameState(sv)
        console = Console(file=StringIO(), force_terminal=True)
        renderer = CLIRenderer(console)
        runner = ChapterRunner(chapter, state, renderer, input_fn=lambda p: "")
        with pytest.raises(ChapterRunError, match="tidak ditemukan"):
            runner.run(start_scene_id="nonexistent")

    def test_playthrough_lapor_terus(self):
        """Full playthrough: ch1(anomali) → ch2(bicara+lapor) → ch3a(terus) → ch4a(pertahankan) → ch5(simpan) → ch6 → END."""
        state = GameState.new_playthrough("t", "01_pembukaan", "")

        next_ch = run_chapter("01_pembukaan", state, ["", "", "", "1"])
        assert state.get_flag("melihat_anomali") is True
        assert next_ch == "02_gejala"

        next_ch = run_chapter("02_gejala", state, ["", "", "1", "", "1"])
        assert state.get_flag("berbicara_dengan_jaya") is True
        assert state.get_flag("melapor") is True
        assert next_ch == "03a_mandor"

        next_ch = run_chapter("03a_mandor", state, ["", "", "1"])
        assert state.get_flag("terus_mencatat") is True
        assert next_ch == "04a_puncak_lapor"

        next_ch = run_chapter("04a_puncak_lapor", state, ["", "", "2"])
        assert state.get_flag("chapter_4_choice") == "pertahankan"
        assert next_ch == "05_perhitungan"

        next_ch = run_chapter("05_perhitungan", state, ["", "", "", "1"])
        assert state.get_flag("chapter_5_choice") == "simpan"
        assert next_ch == "06_penutup"

        next_ch = run_chapter("06_penutup", state, ["", ""])
        assert next_ch == "07_akibat"

    def test_playthrough_diam_robek(self):
        """Full playthrough: ch1(abaikan) → ch2(diam+diam) → ch3b(robek) → ch4d(terima) → ch5(hancurkan) → ch6 → ch7."""
        state = GameState.new_playthrough("t", "01_pembukaan", "")

        next_ch = run_chapter("01_pembukaan", state, ["", "", "", "2"])
        assert state.get_flag("melihat_anomali") is False
        assert next_ch == "02_gejala"

        next_ch = run_chapter("02_gejala", state, ["", "", "2", "", "2"])
        assert state.get_flag("berbicara_dengan_jaya") is False
        assert state.get_flag("melapor") is False
        assert next_ch == "03b_ungkap"

        next_ch = run_chapter("03b_ungkap", state, ["", "", "2"])
        assert state.get_flag("menyimpan_bukti") is False
        assert next_ch == "04d_puncak_hilang"

        next_ch = run_chapter("04d_puncak_hilang", state, ["", "", "2"])
        assert state.get_flag("chapter_4_choice") == "terima"
        assert next_ch == "05_perhitungan"

        next_ch = run_chapter("05_perhitungan", state, ["", "", "", "2"])
        assert state.get_flag("chapter_5_choice") == "hancurkan"
        assert next_ch == "06_penutup"

        next_ch = run_chapter("06_penutup", state, ["", ""])
        assert next_ch == "07_akibat"

    def test_playthrough_sembunyi_beri(self):
        """Full playthrough: ch1(catat) → ch2(bicara+sembunyikan) → ch3c(beri) → ch4c(gabung) → ch5(simpan) → ch6 → ch7."""
        state = GameState.new_playthrough("t", "01_pembukaan", "")

        next_ch = run_chapter("01_pembukaan", state, ["", "", "", "1"])
        assert state.get_flag("melihat_anomali") is True
        assert next_ch == "02_gejala"

        next_ch = run_chapter("02_gejala", state, ["", "", "1", "", "3"])
        assert state.get_flag("berbicara_dengan_jaya") is True
        assert state.get_flag("sembunyikan_bukti") is True
        assert next_ch == "03c_sembunyi"

        next_ch = run_chapter("03c_sembunyi", state, ["", "", "1"])
        assert state.get_flag("beri_bukti_ke_jaya") is True
        assert next_ch == "04c_puncak_bukti"

        next_ch = run_chapter("04c_puncak_bukti", state, ["", "", "1", "1"])
        assert state.get_flag("chapter_4_choice") == "gabung"
        assert next_ch == "05_perhitungan"

        next_ch = run_chapter("05_perhitungan", state, ["", "", "", "1"])
        assert state.get_flag("chapter_5_choice") == "simpan"
        assert next_ch == "06_penutup"

        next_ch = run_chapter("06_penutup", state, ["", ""])
        assert next_ch == "07_akibat"

    def test_state_advance(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("melapor", True)
        assert state.get_flag("melapor") is True
        state.advance_to("ch2", "s2")
        assert state.current_chapter == "ch2"
        state.mark_chapter_complete("ch1")
        assert "ch1" in state.save_state.chapters_completed

    def test_touch_last_saved(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        old = sv.last_saved
        state.touch_last_saved()
        assert sv.last_saved >= old

    def test_new_playthrough(self):
        state = GameState.new_playthrough("s1", "ch1", "scene_1")
        assert state.save_state.save_id == "s1"
        assert state.current_chapter == "ch1"
        assert state.save_state.playthrough_start == state.save_state.last_saved


class TestSaveManager:
    def test_save_and_load(self, tmp_path):
        sv = SaveState(
            save_id="test_save_001",
            current_chapter="ch1",
            current_scene="s1",
            flags={"test": True},
        )
        save(sv, tmp_path)
        loaded = load("test_save_001", tmp_path)
        assert loaded.save_id == "test_save_001"
        assert loaded.flags["test"] is True

    def test_list_saves(self, tmp_path):
        sv = SaveState(save_id="list_test", current_chapter="ch1", current_scene="s1")
        save(sv, tmp_path)
        saves = list_saves(tmp_path)
        assert "list_test" in saves

    def test_load_nonexistent_raises(self, tmp_path):
        with pytest.raises(SaveLoadError, match="tidak ditemukan"):
            load("nope", tmp_path)

    def test_load_corrupt_file_raises(self, tmp_path):
        path = tmp_path / "corrupt.json"
        path.write_text("NOT JSON {{{", encoding="utf-8")
        with pytest.raises(SaveLoadError):
            load("corrupt", tmp_path)

    def test_list_saves_empty_dir(self, tmp_path):
        assert list_saves(tmp_path) == []

    def test_list_saves_nonexistent_dir(self):
        assert list_saves("/nonexistent/path") == []

    def test_completed_save_round_trips(self, tmp_path):
        sv = SaveState(
            save_id="done",
            current_chapter="06_penutup",
            current_scene="",
            completed=True,
        )
        save(sv, tmp_path)
        loaded = load("done", tmp_path)
        assert loaded.completed is True

    def test_save_version_round_trips(self, tmp_path):
        sv = SaveState(
            save_id="ver_test",
            current_chapter="ch1",
            current_scene="s1",
        )
        save(sv, tmp_path)
        loaded = load("ver_test", tmp_path)
        assert loaded.version == 2

    def test_atomic_save_no_corrupt_on_error(self, tmp_path):
        """If write fails mid-way, no corrupt .json file should remain."""
        sv = SaveState(
            save_id="atomic_test",
            current_chapter="ch1",
            current_scene="s1",
        )
        from muara.engine import save_manager
        original_write = save_manager.Path.write_text

        def failing_write(self, *args, **kwargs):
            raise OSError("Simulated write failure")

        save_manager.Path.write_text = failing_write
        try:
            with pytest.raises(SaveLoadError, match="Gagal menulis"):
                save(sv, tmp_path)
        finally:
            save_manager.Path.write_text = original_write

        final_path = tmp_path / "atomic_test.json"
        tmp_path_artifact = tmp_path / "atomic_test.json.tmp"
        assert not final_path.exists(), "Corrupt save file should not exist"
        assert not tmp_path_artifact.exists(), "Tmp file should be cleaned up"

    def test_save_id_path_traversal_rejected(self):
        with pytest.raises(ValidationError, match="save_id"):
            SaveState(
                save_id="../../etc",
                current_chapter="ch1",
                current_scene="s1",
            )


class TestGameStateConditionEvaluation:
    def test_truthy_check(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("melapor", True)
        assert state.evaluate_condition("melapor") is True

    def test_truthy_check_false(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("melapor", False)
        assert state.evaluate_condition("melapor") is False

    def test_equality_true(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("melapor", True)
        assert state.evaluate_condition("melapor == true") is True
        assert state.evaluate_condition("melapor == false") is False

    def test_equality_false(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("melapor", False)
        assert state.evaluate_condition("melapor == false") is True
        assert state.evaluate_condition("melapor == true") is False

    def test_inequality(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("melapor", True)
        assert state.evaluate_condition("melapor != false") is True
        assert state.evaluate_condition("melapor != true") is False

    def test_string_equality(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("chapter_4_choice", "serahkan")
        assert state.evaluate_condition("chapter_4_choice == serahkan") is True
        assert state.evaluate_condition("chapter_4_choice == pertahankan") is False

    def test_numeric_comparison(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("trust_level", 5)
        assert state.evaluate_condition("trust_level >= 5") is True
        assert state.evaluate_condition("trust_level >= 6") is False
        assert state.evaluate_condition("trust_level <= 5") is True
        assert state.evaluate_condition("trust_level <= 4") is False

    def test_negation(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("melapor", True)
        assert state.evaluate_condition("not melapor") is False
        state.set_flag("melapor", False)
        assert state.evaluate_condition("not melapor") is True

    def test_missing_flag(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        assert state.evaluate_condition("nonexistent") is False
        assert state.evaluate_condition("nonexistent == true") is False

    def test_integer_flag(self):
        sv = SaveState(save_id="t", current_chapter="ch1", current_scene="s1")
        state = GameState(sv)
        state.set_flag("count", 3)
        assert state.evaluate_condition("count == 3") is True
        assert state.evaluate_condition("count >= 3") is True
        assert state.evaluate_condition("count <= 2") is False

from muara.engine.event_scheduler import EventScheduler
from muara.models.world_clock import WorldEvent, EventTrigger, Shift
from muara.models.chapter import Scene, Chapter
from muara.engine.chapter_runner import ChapterRunner

def test_chapter_runner_with_scheduler(fresh_state, make_console, make_renderer):
    event = WorldEvent(
        id="test_event",
        trigger=EventTrigger(shift=Shift.SIANG),
        set_flags=["event_triggered: true"]
    )
    scheduler = EventScheduler([event])
    
    chapter = Chapter(
        id="test_chapter",
        title="Test",
        location="Test",
        date="Test",
        time="Test",
        scenes=[
            Scene(
                id="scene_1",
                text="Text",
                on_exit=["advance_clock(shift)"],
                next_chapter="next_chap"
            )
        ]
    )
    
    # Run with scheduler
    runner = ChapterRunner(chapter, fresh_state, make_renderer(), scheduler=scheduler)
    res = runner.run()
    
    # Event should have triggered because scene_1 on_exit advances clock to SIANG
    assert fresh_state.get_flag("event_triggered") is True
    assert res == "next_chap"


def test_chapter_runner_with_scheduler_no_match(fresh_state, make_console, make_renderer):
    event = WorldEvent(
        id="test_event",
        trigger=EventTrigger(shift=Shift.MALAM), # Won't match
        set_flags=["event_triggered: true"]
    )
    scheduler = EventScheduler([event])
    
    chapter = Chapter(
        id="test_chapter",
        title="Test",
        location="Test",
        date="Test",
        time="Test",
        scenes=[
            Scene(
                id="scene_1",
                text="Text",
                next_chapter="next_chap"
            )
        ]
    )
    
    # Run with scheduler
    runner = ChapterRunner(chapter, fresh_state, make_renderer(), scheduler=scheduler)
    res = runner.run()
    
    # Event should NOT have triggered
    assert fresh_state.get_flag("event_triggered") is None
    assert res == "next_chap"

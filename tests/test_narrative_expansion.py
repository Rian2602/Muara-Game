"""Tests for narrative expansion chapters (07-11)."""

from pathlib import Path

import pytest

from muara.engine.chapter_loader import load_chapter, load_manifest
from muara.engine.chapter_runner import ChapterRunner
from muara.engine.state import GameState
from muara.models.save_state import SaveState
from muara.constants import END_OF_STORY_MARKER

from io import StringIO
from rich.console import Console

CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "content" / "chapters"
CONTENT_DIR = CHAPTERS_DIR.parent

NEW_CHAPTERS = [
    "07_akibat",
    "08_tekanan",
    "09_pilihan_sulit",
    "10_konfrontasi",
    "11_warisan",
]


def make_runner(
    chapter_id: str,
    scene_id: str = "scene_1",
    flags: dict | None = None,
    input_values: list[str] | None = None,
):
    """Create a ChapterRunner with scripted input for testing."""
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

    input_iter = iter(input_values) if input_values else iter([])

    def scripted_input(prompt: str = "") -> str:
        try:
            return next(input_iter)
        except StopIteration:
            raise RuntimeError("Scripted input exhausted — more input values needed")

    return ChapterRunner(chapter, state, console, input_fn=scripted_input), state, console


def run_chapter(chapter_id: str, state: GameState, input_sequence: list[str]) -> str | None:
    """Run a single chapter with scripted input, return next_chapter."""
    path = CHAPTERS_DIR / f"{chapter_id}.yaml"
    chapter = load_chapter(path)
    console = Console(file=StringIO(), force_terminal=True)
    input_iter = iter(input_sequence)

    def scripted_input(prompt: str = "") -> str:
        try:
            return next(input_iter)
        except StopIteration:
            raise RuntimeError("Scripted input exhausted — more input values needed")

    runner = ChapterRunner(chapter, state, console, input_fn=scripted_input)
    return runner.run()


class TestNewChapterStructure:
    """Test that new chapters exist and have valid structure."""

    @pytest.mark.parametrize("chapter_id", NEW_CHAPTERS)
    def test_chapter_file_exists(self, chapter_id: str):
        """Each new chapter must have a YAML file."""
        path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        assert path.exists(), f"Chapter file {chapter_id}.yaml not found"

    @pytest.mark.parametrize("chapter_id", NEW_CHAPTERS)
    def test_chapter_loads_and_validates(self, chapter_id: str):
        """Each new chapter YAML must parse and pass all Pydantic validators."""
        path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        chapter = load_chapter(path)
        assert chapter.id == chapter_id
        assert len(chapter.scenes) >= 3, f"Chapter {chapter_id} must have at least 3 scenes"
        assert chapter.title.strip()
        assert chapter.location.strip()

    @pytest.mark.parametrize("chapter_id", NEW_CHAPTERS)
    def test_all_scene_refs_resolve(self, chapter_id: str):
        """Every ChoiceOption.next must point to a scene that exists in the chapter."""
        path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        chapter = load_chapter(path)
        scene_ids = {s.id for s in chapter.scenes}

        for scene in chapter.scenes:
            if scene.choice is not None:
                for option in scene.choice.options:
                    assert option.next in scene_ids, (
                        f"{chapter_id}/{scene.id}: option {option.id!r} "
                        f"points to {option.next!r} which does not exist"
                    )

    @pytest.mark.parametrize("chapter_id", NEW_CHAPTERS)
    def test_no_dead_end_scenes(self, chapter_id: str):
        """Every scene must either have a choice, a next_chapter, or a next scene."""
        path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        chapter = load_chapter(path)

        for i, scene in enumerate(chapter.scenes):
            has_choice = scene.choice is not None
            has_next_chapter = scene.next_chapter is not None
            has_next_scene = i < len(chapter.scenes) - 1

            assert has_choice or has_next_chapter or has_next_scene, (
                f"{chapter_id}/{scene.id}: no choice, no next_chapter, "
                f"and no next scene — dead-end"
            )

    @pytest.mark.parametrize("chapter_id", NEW_CHAPTERS)
    def test_chapter_in_manifest(self, chapter_id: str):
        """Each new chapter must be listed in manifest.yaml."""
        manifest = load_manifest(CONTENT_DIR)
        assert chapter_id in manifest, (
            f"Chapter {chapter_id!r} not in manifest.yaml"
        )


class TestNewFlags:
    """Test that new flags are properly used in chapters."""

    def test_ancaman_diketahui_flag_used(self):
        """Flag ancaman_diketahui must be set in chapter 07."""
        path = CHAPTERS_DIR / "07_akibat.yaml"
        chapter = load_chapter(path)
        
        # Check that at least one choice sets this flag
        flag_found = False
        for scene in chapter.scenes:
            if scene.choice:
                for option in scene.choice.options:
                    if option.set_flags:
                        for flag_str in option.set_flags:
                            if "ancaman_diketahui" in flag_str:
                                flag_found = True
        assert flag_found, "Flag ancaman_diketahui not set in chapter 07"

    def test_percaya_jaya_flag_used(self):
        """Flag percaya_jaya must be set in chapter 08."""
        path = CHAPTERS_DIR / "08_tekanan.yaml"
        chapter = load_chapter(path)
        
        flag_found = False
        for scene in chapter.scenes:
            if scene.choice:
                for option in scene.choice.options:
                    if option.set_flags:
                        for flag_str in option.set_flags:
                            if "percaya_jaya" in flag_str:
                                flag_found = True
        assert flag_found, "Flag percaya_jaya not set in chapter 08"

    def test_pengorbanan_flag_used(self):
        """Flag pengorbanan must be set in chapter 09."""
        path = CHAPTERS_DIR / "09_pilihan_sulit.yaml"
        chapter = load_chapter(path)
        
        flag_found = False
        for scene in chapter.scenes:
            if scene.choice:
                for option in scene.choice.options:
                    if option.set_flags:
                        for flag_str in option.set_flags:
                            if "pengorbanan" in flag_str:
                                flag_found = True
        assert flag_found, "Flag pengorbanan not set in chapter 09"


class TestNewEndings:
    """Test that new endings are reachable."""

    def test_chapter_11_has_ending(self):
        """Chapter 11 must end with END_OF_STORY_MARKER."""
        path = CHAPTERS_DIR / "11_warisan.yaml"
        chapter = load_chapter(path)
        
        # Last scene should have next_chapter = END_OF_STORY_MARKER
        last_scene = chapter.scenes[-1]
        assert last_scene.next_chapter == END_OF_STORY_MARKER, (
            f"Chapter 11 last scene must end with {END_OF_STORY_MARKER}"
        )

    def test_chapter_10_leads_to_11(self):
        """Chapter 10 must lead to chapter 11."""
        path = CHAPTERS_DIR / "10_konfrontasi.yaml"
        chapter = load_chapter(path)
        
        # At least one scene should lead to chapter 11
        leads_to_11 = False
        for scene in chapter.scenes:
            if scene.next_chapter == "11_warisan":
                leads_to_11 = True
        assert leads_to_11, "Chapter 10 must have at least one path to chapter 11"


class TestPlaythroughNewChapters:
    """Test playthrough through new chapters."""

    def test_happy_path_through_new_chapters(self):
        """Test happy path: all positive choices through chapters 07-11."""
        state = GameState.new_playthrough("t", "07_akibat", "")
        state.set_flag("chapter_5_choice", "simpan")
        state.set_flag("melihat_anomali", True)
        state.set_flag("berbicara_dengan_jaya", True)
        state.set_flag("trust_level", 5)

        # Ch07: scene_1 → scene_2 → scene_3(hadapi→4a) → 4a → 4b → 4c → scene_5(terus_catat→6)
        next_ch = run_chapter("07_akibat", state, ["", "", "1", "", "", "", "1"])
        assert next_ch == "08_tekanan"

        # Ch08: scene_1 → scene_2 → scene_2b → scene_3(percaya→4) → 4 → scene_5(tunggu→5a)
        next_ch = run_chapter("08_tekanan", state, ["", "", "", "1", "", "1"])
        assert next_ch == "09_pilihan_sulit"

        # Ch09: scene_1 → scene_2 → scene_3(ambil_bukti→4a) → 4a (next_chapter)
        next_ch = run_chapter("09_pilihan_sulit", state, ["", "", "1"])
        assert next_ch == "10_konfrontasi"

        # Ch10: scene_1 → scene_2 → scene_3(terima→4) → 4 → scene_5
        next_ch = run_chapter("10_konfrontasi", state, ["", "", "1", ""])
        assert next_ch == "11_warisan"

        # Ch11: scene_1 → scene_2(simpan→3) → 3 → 4 → 5
        next_ch = run_chapter("11_warisan", state, ["", "1", "", ""])
        assert next_ch == END_OF_STORY_MARKER

    def test_failure_path_through_new_chapters(self):
        """Test failure path: negative choices lead to consequences."""
        state = GameState.new_playthrough("t", "07_akibat", "")
        state.set_flag("chapter_5_choice", "hancurkan")
        state.set_flag("melihat_anomali", False)
        state.set_flag("trust_level", 2)

        # Ch07: scene_1 → scene_2 → scene_3(hindari→4b) → 4b → 4c → scene_5(berhenti→5b)
        next_ch = run_chapter("07_akibat", state, ["", "", "2", "", "", "3"])
        assert next_ch == "08_tekanan"

        # Ch08: scene_1 → scene_2 → scene_2b → scene_3(tolak→4) → 4 → scene_5(berhenti→5b)
        next_ch = run_chapter("08_tekanan", state, ["", "", "", "2", "", "3"])
        assert next_ch == "09_pilihan_sulit"

        # Ch09: scene_1 → scene_2 → scene_3(biarkan→4b) → 4b (next_chapter)
        next_ch = run_chapter("09_pilihan_sulit", state, ["", "", "2"])
        assert next_ch == "10_konfrontasi"

        # Ch10: scene_1 → scene_2 → scene_3(tolak→4) → 4 → scene_5
        next_ch = run_chapter("10_konfrontasi", state, ["", "", "2", ""])
        assert next_ch == "11_warisan"

        # Ch11: scene_1 → scene_2(hancurkan→3) → 3 → 4 → 5
        next_ch = run_chapter("11_warisan", state, ["", "2", "", ""])
        assert next_ch == END_OF_STORY_MARKER

    def test_mixed_path_through_new_chapters(self):
        """Test mixed path: some positive, some negative choices."""
        state = GameState.new_playthrough("t", "07_akibat", "")
        state.set_flag("chapter_5_choice", "simpan")
        state.set_flag("melihat_anomali", True)
        state.set_flag("berbicara_dengan_jaya", True)
        state.set_flag("trust_level", 3)

        # Ch07: hadapi → terus_catat
        next_ch = run_chapter("07_akibat", state, ["", "", "1", "", "", "", "1"])
        assert next_ch == "08_tekanan"

        # Ch08: percaya_jaya → berhenti (mixed: trust Jaya but stop recording)
        next_ch = run_chapter("08_tekanan", state, ["", "", "", "1", "", "3"])
        assert next_ch == "09_pilihan_sulit"

        # Ch09: berikan_jaya (mixed: trust but give evidence away)
        next_ch = run_chapter("09_pilihan_sulit", state, ["", "", "3"])
        assert next_ch == "10_konfrontasi"

        # Ch10: tolak (negative: refuse mandor's evidence)
        next_ch = run_chapter("10_konfrontasi", state, ["", "", "2", ""])
        assert next_ch == "11_warisan"

        # Ch11: simpan (positive: keep the book)
        next_ch = run_chapter("11_warisan", state, ["", "1", "", ""])
        assert next_ch == END_OF_STORY_MARKER


class TestFlagActivation:
    """Test that newly activated flags are properly checked."""

    def test_respon_ancaman_checked_in_ch07_scene5(self):
        """Flag respon_ancaman must be checked in ch07 scene_5 text_variants."""
        path = CHAPTERS_DIR / "07_akibat.yaml"
        chapter = load_chapter(path)

        scene_5 = chapter.get_scene("scene_5")
        assert scene_5.text_variants, "scene_5 must have text_variants"
        conditions = [v.condition for v in scene_5.text_variants]
        assert any("respon_ancaman" in c for c in conditions), (
            "scene_5 text_variants must check respon_ancaman"
        )

    def test_respon_ancaman_checked_in_ch08_scene1(self):
        """Flag respon_ancaman must be checked in ch08 scene_1 text_variants."""
        path = CHAPTERS_DIR / "08_tekanan.yaml"
        chapter = load_chapter(path)

        scene_1 = chapter.get_scene("scene_1")
        assert scene_1.text_variants, "scene_1 must have text_variants"
        conditions = [v.condition for v in scene_1.text_variants]
        assert any("respon_ancaman" in c for c in conditions), (
            "scene_1 text_variants must check respon_ancaman"
        )

    def test_pengorbanan_checked_in_ch10_scene1(self):
        """Flag pengorbanan must be checked in ch10 scene_1 text_variants."""
        path = CHAPTERS_DIR / "10_konfrontasi.yaml"
        chapter = load_chapter(path)

        scene_1 = chapter.get_scene("scene_1")
        assert scene_1.text_variants, "scene_1 must have text_variants"
        conditions = [v.condition for v in scene_1.text_variants]
        assert any("pengorbanan" in c for c in conditions), (
            "scene_1 text_variants must check pengorbanan"
        )

    def test_percaya_jaya_checked_in_ch09_scene1(self):
        """Flag percaya_jaya must be checked in ch09 scene_1 text_variants."""
        path = CHAPTERS_DIR / "09_pilihan_sulit.yaml"
        chapter = load_chapter(path)

        scene_1 = chapter.get_scene("scene_1")
        assert scene_1.text_variants, "scene_1 must have text_variants"
        conditions = [v.condition for v in scene_1.text_variants]
        assert any("percaya_jaya" in c for c in conditions), (
            "scene_1 text_variants must check percaya_jaya"
        )

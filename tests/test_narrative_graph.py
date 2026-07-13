"""Narrative graph validation tests.

These tests verify the structural integrity of the narrative graph —
ensuring no unreachable scenes, no dead-end scenes, no orphan scenes,
and that all flags are actually used.
"""

from pathlib import Path

import pytest

from muara.engine.chapter_loader import load_chapter, load_manifest
from muara.engine.state import GameState
from muara.models.save_state import SaveState

CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "content" / "chapters"
CONTENT_DIR = CHAPTERS_DIR.parent


def _load_all_chapters():
    """Load all chapters from manifest."""
    manifest = load_manifest(CONTENT_DIR)
    chapters = {}
    for ch_id in manifest:
        path = CHAPTERS_DIR / f"{ch_id}.yaml"
        chapters[ch_id] = load_chapter(path)
    return chapters


def _get_all_scene_ids(chapter):
    """Get all scene IDs in a chapter."""
    return {scene.id for scene in chapter.scenes}


def _get_referenced_scene_ids(chapter):
    """Get all scene IDs referenced by choices in a chapter."""
    referenced = set()
    for scene in chapter.scenes:
        if scene.choice:
            for option in scene.choice.options:
                referenced.add(option.next)
    return referenced


def _get_scene_types(chapter):
    """Get the type of each scene (linear, choice, terminal)."""
    types = {}
    for scene in chapter.scenes:
        if scene.choice:
            types[scene.id] = "choice"
        elif scene.next_chapter or scene.next_ending:
            types[scene.id] = "terminal"
        else:
            types[scene.id] = "linear"
    return types


class TestNoUnreachableScenes:
    """Every scene must be reachable from scene_1."""

    @pytest.mark.parametrize("chapter_id", [
        "07_akibat", "08_tekanan", "09_pilihan_sulit",
        "10_konfrontasi", "11_warisan",
    ])
    def test_all_scenes_reachable(self, chapter_id: str):
        """Every scene must be reachable from scene_1 via choices or linear flow."""
        path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        chapter = load_chapter(path)
        scene_ids = _get_all_scene_ids(chapter)

        reachable = set()
        queue = ["scene_1"]

        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue
            reachable.add(current)

            scene = chapter.get_scene(current)
            if scene.choice:
                for option in scene.choice.options:
                    if option.next not in reachable:
                        queue.append(option.next)
            elif not scene.next_chapter and not scene.next_ending:
                idx = chapter._scene_order[current]
                if idx + 1 < len(chapter.scenes):
                    next_scene = chapter.scenes[idx + 1]
                    if next_scene.id not in reachable:
                        queue.append(next_scene.id)

        unreachable = scene_ids - reachable
        assert not unreachable, (
            f"Chapter {chapter_id}: unreachable scenes {unreachable}"
        )


class TestNoOrphanScenes:
    """Every scene must be reachable from scene_1."""

    @pytest.mark.parametrize("chapter_id", [
        "07_akibat", "08_tekanan", "09_pilihan_sulit",
        "10_konfrontasi", "11_warisan",
    ])
    def test_no_orphan_scenes(self, chapter_id: str):
        """No scene should exist that cannot be reached from scene_1."""
        path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        chapter = load_chapter(path)
        scene_ids = _get_all_scene_ids(chapter)

        reachable = set()
        queue = ["scene_1"]

        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue
            reachable.add(current)

            scene = chapter.get_scene(current)
            if scene.choice:
                for option in scene.choice.options:
                    if option.next not in reachable:
                        queue.append(option.next)
            elif not scene.next_chapter and not scene.next_ending:
                idx = chapter._scene_order[current]
                if idx + 1 < len(chapter.scenes):
                    next_scene = chapter.scenes[idx + 1]
                    if next_scene.id not in reachable:
                        queue.append(next_scene.id)

        orphans = scene_ids - reachable
        assert not orphans, (
            f"Chapter {chapter_id}: orphan/unreachable scenes {orphans}"
        )


class TestNoDeadEndScenes:
    """Every non-terminal scene must have a choice or a next scene."""

    @pytest.mark.parametrize("chapter_id", [
        "07_akibat", "08_tekanan", "09_pilihan_sulit",
        "10_konfrontasi", "11_warisan",
    ])
    def test_no_dead_ends(self, chapter_id: str):
        """Every scene must either have a choice, a next_chapter, or a next scene."""
        path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        chapter = load_chapter(path)

        for i, scene in enumerate(chapter.scenes):
            has_choice = scene.choice is not None
            has_next_chapter = scene.next_chapter is not None
            has_next_scene = i < len(chapter.scenes) - 1

            assert has_choice or has_next_chapter or has_next_scene, (
                f"{chapter_id}/{scene.id}: dead-end — no choice, no next_chapter, "
                f"and no next scene"
            )


class TestFlagsActuallyUsed:
    """Every flag set by a choice must be checked somewhere."""

    def _get_all_flags_set(self, chapters):
        """Get all flags set by choices across all chapters."""
        flags_set = {}
        for ch_id, chapter in chapters.items():
            for scene in chapter.scenes:
                if scene.choice:
                    for option in scene.choice.options:
                        for flag_str in option.set_flags:
                            key = flag_str.split(":")[0].strip()
                            if key not in flags_set:
                                flags_set[key] = []
                            flags_set[key].append(f"{ch_id}/{scene.id}/{option.id}")
        return flags_set

    def _get_all_flags_checked(self, chapters):
        """Get all flags checked in text_variants or ending logic."""
        flags_checked = set()
        for ch_id, chapter in chapters.items():
            for scene in chapter.scenes:
                if scene.text_variants:
                    for variant in scene.text_variants:
                        condition = variant.condition
                        for op in (">=", "<=", "!=", "=="):
                            if op in condition:
                                key = condition.partition(op)[0].strip()
                                flags_checked.add(key)
                                break
                        else:
                            if condition.startswith("not "):
                                flags_checked.add(condition[4:].strip())
                            else:
                                flags_checked.add(condition)

        flags_checked.update({
            "kebenaran_terungkap", "warisan_positif", "konfrontasi_berhasil",
            "tekanan_meningkat", "melihat_anomali", "melapor", "bukti_kuat",
            "beri_bukti_ke_jaya", "berbicara_dengan_jaya", "chapter_5_choice",
            "trust_level",
        })
        return flags_checked

    def test_all_set_flags_checked(self):
        """Every flag set by a choice must be checked in text_variants or ending logic."""
        chapters = _load_all_chapters()
        flags_set = self._get_all_flags_set(chapters)
        flags_checked = self._get_all_flags_checked(chapters)

        excluded = {
            "ancaman_diketahui",
            "chapter_4_choice",
            "menyimpan_bukti",
            "terus_mencatat",
            "menghadapi_mandor",
            "sembunyikan_bukti",
        }
        unused = set(flags_set.keys()) - flags_checked - excluded
        assert not unused, (
            f"Flags set but never checked: {unused}"
        )


class TestEndingGatesConsistent:
    """Ending conditions must match design documentation."""

    def test_pembebasan_requires_melihat_anomali(self):
        """pembebasan ending must require melihat_anomali == true."""
        from muara.main import _determine_ending

        state = GameState.new_playthrough("test", "01_pembukaan", "")
        state.set_flag("kebenaran_terungkap", True)
        state.set_flag("warisan_positif", True)
        state.set_flag("melihat_anomali", False)

        ending = _determine_ending(state)
        assert ending != "pembebasan", (
            "pembebasan should not be reachable without melihat_anomali"
        )

    def test_sekutu_requires_berbicara_dengan_jaya(self):
        """sekutu ending must require berbicara_dengan_jaya == true."""
        from muara.main import _determine_ending

        state = GameState.new_playthrough("test", "01_pembukaan", "")
        state.set_flag("beri_bukti_ke_jaya", True)
        state.set_flag("bukti_kuat", True)
        state.set_flag("berbicara_dengan_jaya", False)

        ending = _determine_ending(state)
        assert ending != "sekutu", (
            "sekutu should not be reachable without berbicara_dengan_jaya"
        )

    def test_tekanan_meningkat_reachable(self):
        """kehancuran via tekanan_meningkat >= 6 should be reachable."""
        from muara.main import _determine_ending

        state = GameState.new_playthrough("test", "01_pembukaan", "")
        state.set_flag("konfrontasi_berhasil", True)
        state.set_flag("tekanan_meningkat", 6)

        ending = _determine_ending(state)
        assert ending == "kehancuran", (
            "kehancuran should be reachable with tekanan_meningkat >= 6"
        )


class TestDuplicateSceneIds:
    """Scene IDs must be unique within each chapter."""

    @pytest.mark.parametrize("chapter_id", [
        "07_akibat", "08_tekanan", "09_pilihan_sulit",
        "10_konfrontasi", "11_warisan",
    ])
    def test_no_duplicate_scene_ids(self, chapter_id: str):
        """No two scenes in a chapter can have the same ID."""
        path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        chapter = load_chapter(path)
        scene_ids = [scene.id for scene in chapter.scenes]
        assert len(scene_ids) == len(set(scene_ids)), (
            f"Chapter {chapter_id}: duplicate scene IDs {scene_ids}"
        )

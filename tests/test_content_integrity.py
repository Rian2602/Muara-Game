"""Content integrity: validates ALL chapters from manifest at test time."""

from pathlib import Path

import pytest

from muara.engine.chapter_loader import load_chapter, load_manifest
from muara.models.chapter import Chapter

CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "content" / "chapters"
CONTENT_DIR = CHAPTERS_DIR.parent


def _chapter_ids() -> list[str]:
    return load_manifest(CONTENT_DIR)


@pytest.mark.parametrize("chapter_id", _chapter_ids(), ids=lambda c: c)
def test_chapter_loads_and_validates(chapter_id: str):
    """Each chapter YAML must parse and pass all Pydantic validators."""
    path = CHAPTERS_DIR / f"{chapter_id}.yaml"
    chapter = load_chapter(path)
    assert chapter.id == chapter_id
    assert len(chapter.scenes) >= 1
    assert chapter.title.strip()
    assert chapter.location.strip()


@pytest.mark.parametrize("chapter_id", _chapter_ids(), ids=lambda c: c)
def test_all_scene_refs_resolve(chapter_id: str):
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


@pytest.mark.parametrize("chapter_id", _chapter_ids(), ids=lambda c: c)
def test_no_dead_end_scenes(chapter_id: str):
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


@pytest.mark.parametrize("chapter_id", _chapter_ids(), ids=lambda c: c)
def test_chapter_in_manifest(chapter_id: str):
    """Each chapter file's id must appear in content/manifest.yaml."""
    manifest = load_manifest(CONTENT_DIR)
    assert chapter_id in manifest, (
        f"Chapter {chapter_id!r} ada di content/chapters/ tapi tidak di manifest.yaml. "
        f"Tambahkan ke manifest di posisi naratif yang tepat."
    )


def test_manifest_chapters_all_have_files():
    """Each entry in manifest.yaml must have a corresponding YAML file."""
    manifest = load_manifest(CONTENT_DIR)
    for chapter_id in manifest:
        expected_path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        assert expected_path.exists(), (
            f"manifest.yaml mencantumkan {chapter_id!r} tapi file "
            f"'{expected_path.name}' tidak ditemukan di content/chapters/."
        )


def test_no_orphan_yaml_files():
    """No .yaml in content/chapters/ should be unlisted in manifest."""
    manifest = load_manifest(CONTENT_DIR)
    manifest_set = set(manifest)
    for yaml_file in sorted(CHAPTERS_DIR.glob("*.yaml")):
        chapter_id = yaml_file.stem
        assert chapter_id in manifest_set, (
            f"File '{yaml_file.name}' ada di content/chapters/ tapi tidak "
            f"terdaftar di manifest.yaml. Tambahkan atau hapus file ini."
        )

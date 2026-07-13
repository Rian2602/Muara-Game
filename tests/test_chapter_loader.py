"""Verifikasi chapter_loader: YAML loading, manifest, error handling."""

from pathlib import Path

import pytest
import yaml

from muara.engine.chapter_loader import (
    ChapterLoadError,
    load_all_chapters,
    load_chapter,
    load_manifest,
)
from muara.models.chapter import Chapter

CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "content" / "chapters"


def _write_yaml(tmp_path: Path, filename: str, content: dict) -> Path:
    path = tmp_path / filename
    path.write_text(yaml.dump(content), encoding="utf-8")
    return path


VALID_CHAPTER_DICT = {
    "id": "01_test",
    "title": "TEST CHAPTER",
    "location": "Lokasi Uji",
    "date": "1 Januari 1900",
    "time": "00.00",
    "scenes": [{"id": "scene_1", "text": "Teks pembuka."}],
}


class TestLoadChapter:
    def test_valid_file(self, tmp_path):
        path = _write_yaml(tmp_path, "01_test.yaml", VALID_CHAPTER_DICT)
        chapter = load_chapter(path)
        assert chapter.id == "01_test"
        assert chapter.title == "TEST CHAPTER"

    def test_file_not_found(self):
        with pytest.raises(ChapterLoadError, match="tidak ditemukan"):
            load_chapter(Path("/nonexistent.yaml"))

    def test_invalid_yaml_syntax(self, tmp_path):
        path = tmp_path / "rusak.yaml"
        path.write_text("id: [ini bukan yaml valid: {{{", encoding="utf-8")
        with pytest.raises(ChapterLoadError):
            load_chapter(path)

    def test_empty_file(self, tmp_path):
        path = tmp_path / "kosong.yaml"
        path.write_text("", encoding="utf-8")
        with pytest.raises(ChapterLoadError, match="kosong"):
            load_chapter(path)

    def test_missing_required_field(self, tmp_path):
        invalid = dict(VALID_CHAPTER_DICT)
        del invalid["location"]
        path = _write_yaml(tmp_path, "invalid.yaml", invalid)
        with pytest.raises(ChapterLoadError, match="Skema bab tidak valid"):
            load_chapter(path)

    def test_error_message_includes_path(self, tmp_path):
        path = tmp_path / "spesifik.yaml"
        path.write_text("", encoding="utf-8")
        with pytest.raises(ChapterLoadError, match="spesifik.yaml"):
            load_chapter(path)

    def test_placeholder_loads(self):
        path = CHAPTERS_DIR / "01_pembukaan.yaml"
        chapter = load_chapter(path)
        assert chapter.id == "01_pembukaan"
        assert len(chapter.scenes) >= 3


class TestLoadManifest:
    def test_valid_manifest(self, tmp_path):
        path = _write_yaml(tmp_path, "manifest.yaml", {"chapters": ["01_a", "02_b"]})
        result = load_manifest(tmp_path)
        assert result == ["01_a", "02_b"]

    def test_empty_chapters_list_valid(self, tmp_path):
        _write_yaml(tmp_path, "manifest.yaml", {"chapters": []})
        result = load_manifest(tmp_path)
        assert result == []

    def test_missing_chapters_key_raises(self, tmp_path):
        _write_yaml(tmp_path, "manifest.yaml", {"not_chapters": []})
        with pytest.raises(ChapterLoadError, match="chapters"):
            load_manifest(tmp_path)

    def test_file_not_found(self, tmp_path):
        with pytest.raises(ChapterLoadError):
            load_manifest(tmp_path / "nonexistent")

    def test_chapters_not_list_raises(self, tmp_path):
        _write_yaml(tmp_path, "manifest.yaml", {"chapters": "not_a_list"})
        with pytest.raises(ChapterLoadError):
            load_manifest(tmp_path)


class TestLoadAllChapters:
    def test_multiple_valid_files(self, tmp_path):
        d = tmp_path / "chapters"
        d.mkdir()
        a = dict(VALID_CHAPTER_DICT); a["id"] = "01_a"
        b = dict(VALID_CHAPTER_DICT); b["id"] = "02_b"
        _write_yaml(d, "01_a.yaml", a)
        _write_yaml(d, "02_b.yaml", b)
        result = load_all_chapters(d)
        assert set(result.keys()) == {"01_a", "02_b"}

    def test_duplicate_id_raises(self, tmp_path):
        d = tmp_path / "chapters"
        d.mkdir()
        _write_yaml(d, "01_a.yaml", VALID_CHAPTER_DICT)
        _write_yaml(d, "01_a_copy.yaml", VALID_CHAPTER_DICT)
        with pytest.raises(ChapterLoadError, match="duplikat"):
            load_all_chapters(d)

    def test_empty_directory(self, tmp_path):
        d = tmp_path / "chapters"
        d.mkdir()
        result = load_all_chapters(d)
        assert result == {}

    def test_directory_not_found(self, tmp_path):
        with pytest.raises(ChapterLoadError, match="tidak ditemukan"):
            load_all_chapters(tmp_path / "nonexistent")

    def test_manifest_chapters_all_load(self):
        from muara.engine.chapter_loader import load_manifest

        manifest_path = Path(__file__).resolve().parent.parent / "content"
        chapter_ids = load_manifest(manifest_path)
        assert len(chapter_ids) > 0

        for cid in chapter_ids:
            path = CHAPTERS_DIR / f"{cid}.yaml"
            chapter = load_chapter(path)
            assert chapter.id == cid
            assert len(chapter.scenes) >= 1

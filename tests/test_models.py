"""Verifikasi model pydantic: Chapter, Scene, Choice, FlagAssignment, SaveState."""

import pytest
from pydantic import ValidationError

from muara.models.chapter import Chapter, Choice, ChoiceOption, FlagAssignment, Scene
from muara.models.save_state import SaveState


VALID_CHAPTER_DICT = {
    "id": "test_chapter",
    "title": "TEST TITLE",
    "location": "Test Location",
    "date": "1 Januari 1900",
    "time": "00.00",
    "scenes": [
        {"id": "scene_1", "text": "Scene one text."},
        {
            "id": "scene_2",
            "text": "Scene two with choice.",
            "choice": {
                "prompt": "What do you do?",
                "options": [
                    {"id": "opt_a", "label": "Option A", "next": "scene_1", "set_flags": ["flag_a: true"]},
                    {"id": "opt_b", "label": "Option B", "next": "scene_1"},
                ],
            },
        },
        {"id": "scene_3", "text": "Scene three.", "next_chapter": "next_chapter_id"},
    ],
}

VALID_SAVE_DICT = {
    "save_id": "save_001",
    "player_name": "Test Player",
    "current_chapter": "test_chapter",
    "current_scene": "scene_1",
    "flags": {"flag_a": True, "counter": 42},
    "chapters_completed": ["prev_chapter"],
}


class TestFlagAssignment:
    def test_parses_bool_true(self):
        flag = FlagAssignment.from_raw_string("melapor_ke_mandor: true")
        assert flag.key == "melapor_ke_mandor"
        assert flag.value is True

    def test_parses_bool_false(self):
        flag = FlagAssignment.from_raw_string("contoh_flag: false")
        assert flag.value is False

    def test_parses_int(self):
        flag = FlagAssignment.from_raw_string("kunjungan_count: 3")
        assert flag.value == 3
        assert isinstance(flag.value, int)

    def test_parses_string_fallback(self):
        flag = FlagAssignment.from_raw_string("nama_saksi: Darma")
        assert flag.value == "Darma"

    def test_missing_colon_raises_value_error(self):
        with pytest.raises(ValueError):
            FlagAssignment.from_raw_string("tidak_ada_titik_dua")

    def test_parses_negative_int(self):
        flag = FlagAssignment.from_raw_string("offset: -5")
        assert flag.value == -5
        assert isinstance(flag.value, int)

    def test_string_fallback_for_non_int(self):
        flag = FlagAssignment.from_raw_string("status: --5")
        assert flag.value == "--5"
        assert isinstance(flag.value, str)

    def test_value_with_colon_in_string(self):
        """Nilai yang mengandung ':' setelah colon pertama tetap terbaca."""
        flag = FlagAssignment.from_raw_string("url: http://example.com")
        assert flag.key == "url"
        assert flag.value == "http://example.com"


class TestChapterModel:
    def test_valid_chapter_from_dict(self):
        ch = Chapter.model_validate(VALID_CHAPTER_DICT)
        assert ch.id == "test_chapter"
        assert len(ch.scenes) == 3
        assert ch.scenes[0].choice is None

    def test_scene_with_choice(self):
        ch = Chapter.model_validate(VALID_CHAPTER_DICT)
        scene = ch.scenes[1]
        assert scene.choice is not None
        assert len(scene.choice.options) == 2
        assert scene.choice.options[0].set_flags == ["flag_a: true"]

    def test_scene_with_next_chapter(self):
        ch = Chapter.model_validate(VALID_CHAPTER_DICT)
        assert ch.scenes[2].next_chapter == "next_chapter_id"

    def test_extra_field_rejected(self):
        bad = {**VALID_CHAPTER_DICT, "bogus_field": "nope"}
        with pytest.raises(ValidationError):
            Chapter.model_validate(bad)

    def test_missing_required_field(self):
        bad = {"id": "x"}
        with pytest.raises(ValidationError):
            Chapter.model_validate(bad)

    def test_choice_single_option_raises(self):
        with pytest.raises(ValidationError):
            Choice(
                prompt="Cuma satu?",
                options=[ChoiceOption(id="a", label="Satu", next="scene_2")],
            )

    def test_choice_duplicate_option_ids_raises(self):
        with pytest.raises(ValidationError):
            Choice(
                prompt="Duplikat",
                options=[
                    ChoiceOption(id="a", label="Pertama", next="scene_2a"),
                    ChoiceOption(id="a", label="Kedua", next="scene_2b"),
                ],
            )

    def test_scene_blank_text_raises(self):
        with pytest.raises(ValidationError):
            Scene(id="scene_1", text="   ")

    def test_chapter_empty_scenes_raises(self):
        with pytest.raises(ValidationError):
            Chapter(
                id="t", title="T", location="L",
                date="1 Januari 1900", time="00.00", scenes=[],
            )

    def test_chapter_duplicate_scene_ids_raises(self):
        with pytest.raises(ValidationError):
            Chapter(
                id="t", title="T", location="L",
                date="1 Januari 1900", time="00.00",
                scenes=[
                    Scene(id="s1", text="Pertama"),
                    Scene(id="s1", text="Duplikat"),
                ],
            )

    def test_scene_choice_and_next_chapter_raises(self):
        with pytest.raises(ValidationError, match="choice.*next_chapter"):
            Scene(
                id="bad_scene",
                text="Scene ini punya keduanya.",
                choice=Choice(
                    prompt="Pilih?",
                    options=[
                        ChoiceOption(id="a", label="A", next="s1"),
                        ChoiceOption(id="b", label="B", next="s1"),
                    ],
                ),
                next_chapter="some_chapter",
            )

    def test_chapter_with_dangling_scene_reference_raises(self):
        with pytest.raises(ValidationError, match="tidak ada di"):
            Chapter(
                id="t", title="T", location="L",
                date="1 Jan 1900", time="00.00",
                scenes=[
                    Scene(id="s1", text="Start", choice=Choice(
                        prompt="?",
                        options=[
                            ChoiceOption(id="a", label="A", next="S_TIDAK_ADA"),
                            ChoiceOption(id="b", label="B", next="s2"),
                        ]
                    )),
                    Scene(id="s2", text="End", next_chapter="__END__"),
                ],
            )

    def test_get_scene_found(self):
        ch = Chapter(
            id="t", title="T", location="L",
            date="1 Januari 1900", time="00.00",
            scenes=[Scene(id="s1", text="Teks.")],
        )
        assert ch.get_scene("s1").text == "Teks."

    def test_get_scene_not_found_raises_key_error(self):
        ch = Chapter(
            id="t", title="T", location="L",
            date="1 Januari 1900", time="00.00",
            scenes=[Scene(id="s1", text="Teks.")],
        )
        with pytest.raises(KeyError):
            ch.get_scene("s_tidak_ada")

    def test_choice_option_parsed_flags(self):
        option = ChoiceOption(
            id="lapor", label="Lapor", next="s3a",
            set_flags=["melapor: true", "count: 1"],
        )
        parsed = option.parsed_flags
        assert len(parsed) == 2
        assert parsed[0].value is True
        assert parsed[1].value == 1


class TestSaveStateModel:
    def test_valid_save_from_dict(self):
        sv = SaveState.model_validate(VALID_SAVE_DICT)
        assert sv.save_id == "save_001"
        assert sv.flags["flag_a"] is True

    def test_defaults_applied(self):
        sv = SaveState(save_id="m", current_chapter="ch1", current_scene="s1")
        assert sv.player_name is None
        assert sv.flags == {}
        assert sv.chapters_completed == []

    def test_extra_field_rejected(self):
        bad = {**VALID_SAVE_DICT, "unknown": 123}
        with pytest.raises(ValidationError):
            SaveState.model_validate(bad)

    def test_version_defaults_to_one(self):
        sv = SaveState(save_id="v", current_chapter="ch1", current_scene="s1")
        assert sv.version == 1

    def test_save_id_rejects_path_traversal(self):
        with pytest.raises(ValidationError, match="save_id"):
            SaveState(
                save_id="../../etc/passwd",
                current_chapter="ch1",
                current_scene="s1",
            )

    def test_save_id_rejects_spaces(self):
        with pytest.raises(ValidationError, match="save_id"):
            SaveState(
                save_id="has spaces",
                current_chapter="ch1",
                current_scene="s1",
            )

    def test_save_id_allows_hyphens_underscores(self):
        sv = SaveState(
            save_id="my-save_01",
            current_chapter="ch1",
            current_scene="s1",
        )
        assert sv.save_id == "my-save_01"

    def test_endings_achieved_defaults_empty(self):
        sv = SaveState(save_id="e", current_chapter="ch1", current_scene="s1")
        assert sv.endings_achieved == []


class TestTextVariantModel:
    def test_scene_with_text_variants(self):
        scene = Scene(
            id="s1",
            text="Fallback.",
            text_variants=[
                {"condition": "flag == true", "text": "Variant A", "default": True},
            ],
            next_chapter="__END__",
        )
        assert len(scene.text_variants) == 1
        assert scene.text_variants[0].condition == "flag == true"
        assert scene.text_variants[0].default is True

    def test_scene_text_variants_requires_default(self):
        with pytest.raises(ValidationError, match="default"):
            Scene(
                id="s1",
                text=".",
                text_variants=[
                    {"condition": "flag == true", "text": "Only variant"},
                ],
                next_chapter="__END__",
            )

    def test_scene_text_and_variants_mutually_exclusive(self):
        with pytest.raises(ValidationError, match="default"):
            Scene(
                id="s1",
                text="Main text",
                text_variants=[
                    {"condition": "flag == true", "text": "Variant"},
                ],
                next_chapter="__END__",
            )

    def test_scene_with_text_no_variants_ok(self):
        scene = Scene(id="s1", text="Hello", next_chapter="__END__")
        assert scene.text_variants is None

    def test_scene_next_ending(self):
        scene = Scene(id="s1", text="End", next_ending="dipercaya")
        assert scene.next_ending == "dipercaya"
        assert scene.next_chapter is None
        assert scene.choice is None

    def test_scene_terminal_mutual_exclusion(self):
        with pytest.raises(ValidationError, match="terminal"):
            Scene(
                id="s1",
                text="Bad",
                next_chapter="__END__",
                next_ending="bad",
            )

    def test_scene_choice_and_ending_exclusive(self):
        with pytest.raises(ValidationError, match="terminal"):
            Scene(
                id="s1",
                text="Bad",
                choice={"prompt": "Pick", "options": [
                    {"id": "a", "label": "A", "next": "s1"},
                    {"id": "b", "label": "B", "next": "s1"},
                ]},
                next_ending="bad",
            )
